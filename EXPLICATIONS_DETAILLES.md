# Explications Détaillées du Système

Ce document explique point par point comment chaque exigence du brief a été implémentée et résolue.

## 1. La Normalisation et la Gestion du "Bruit de Saisie"

Les données d'entreprise accumulées sur des années (CRM, saisies manuelles) sont notoirement sales. Le code situé dans `src/api_tva_meridian/normalize.py` ne se contente pas d'enlever les espaces ou les tirets, il opère un nettoyage intelligent :

1. **Les valeurs "fantômes"** : Des textes comme `"NaN"`, `"NULL"`, `"NONE"` sont souvent importés comme des chaînes de caractères par les outils de data. Notre normaliseur les détecte et les transforme en vrais états `VIDE_OU_NUL`, évitant qu'ils ne soient traités comme des erreurs structurelles incompréhensibles.
2. **La confusion OCR (O/0, I/1)** : C'est une erreur de saisie humaine classique. Lorsqu'un numéro échoue à la validation officielle `stdnum`, le normaliseur tente de réparer le numéro en remplaçant les éventuels "O" par des "0" et les "I" par des "1" dans la section numérique du numéro de TVA. Si la clé de contrôle redevient valide grâce à cette rustine, le numéro est requalifié comme `VALIDE`. Ainsi, le bruit de saisie n'invalide pas bêtement un numéro.

## 2. La Réduction Stratégique des Appels VIES

Le service VIES est gratuit mais fragile (il bloque les utilisateurs abusifs). L'objectif du brief était de réduire mathématiquement la charge. Voici comment c'est garanti :

1. **La barrière structurelle** : Près de 46% du fichier source contient des numéros dont la clé de contrôle ou le format sont faux. Il est inutile d'appeler VIES pour ceux-ci : ils sont bloqués et enregistrés en `INVALIDE` dès l'importation.
2. **La déduplication** : Le code de la campagne VIES (`check_campaign.py`) n'itère pas bêtement sur les lignes. Il requête la base avec une instruction SQL `SELECT DISTINCT numero_tva_normalise`. Ainsi, si un même numéro a été inséré 10 fois par 3 canaux différents, **un seul appel réseau sera effectué**.
3. **Propagation du verdict** : Une fois la réponse VIES reçue, le script met à jour d'un seul coup *toutes* les lignes possédant ce numéro normalisé en base.

Sur 10 000 lignes, nous passons à seulement **5 119 appels réels**, soit une division par 2 de l'empreinte réseau.

## 3. Le Client VIES (Phase 2)

Le client écrit dans `src/api_tva_meridian/vies.py` attaque directement l'**API REST officielle** la plus récente de VIES (`/rest-api/check-vat-number`).

- Il est agnostique et n'a pas besoin de schémas SOAP compliqués.
- Il parse le JSON de retour.
- **Gestion stricte des trois états** :
  - `valid: true` -> `VALIDE`
  - `valid: false` -> `INVALIDE`
  - Toute erreur HTTP, Timeout, ou limitation de service (`MS_MAX_CONCURRENT_REQ`) est attrapée et strictement convertie en état `INDETERMINE`. Une panne de la commission européenne ne transformera jamais un numéro valide en invalide (ce qui empêcherait de facturer le client !).

## 4. Tolérance aux Pannes et Reprise (Campagne)

Le script `check_campaign.py` utilise une requête ciblée :
```sql
WHERE verdict_en_ligne IS NULL OR verdict_en_ligne = 'INDETERMINE'
```
Cette simple clause rend la campagne **invulnérable aux crashs**. Si votre PC s'éteint, ou que vous faites un `CTRL+C`, la prochaine exécution ignorera totalement ce qui a déjà été validé, et réessaiera uniquement ceux qui manquent ou qui avaient échoué lors de la tentative précédente (les `INDETERMINE`).

## 5. L'API REST et le concept de "Fraîcheur"

L'API `src/api_tva_meridian/main.py` est l'organe que la facturation utilise. Son contrat est sophistiqué :

1. **Renvoi Structurel Rapide** : Si le numéro soumis n'a même pas le bon format, l'API ne va même pas embêter la base de données ou VIES, elle coupe court immédiatement et renvoie `INVALIDE (Origine: STRUCTUREL)`.
2. **Le système de Cache (30 jours)** : 
   - L'API vérifie si le numéro est dans notre base. S'il a été vérifié par VIES il y a **moins de 30 jours**, elle le renvoie instantanément.
   - S'il a plus de 30 jours, l'API le considère comme "périmé" et fait un appel réseau en temps réel à VIES pour rafraîchir l'information en base de données.
3. **Le Repli Gracieux** : Que se passe-t-il si un numéro vieux de 8 mois est testé, mais que VIES est hors-ligne aujourd'hui ? Plutôt que de renvoyer `INDETERMINE` et de bloquer la vente, l'API est conçue pour replier intelligemment sur la "vieille" valeur en base. Elle avertit simplement la facturation via les métadonnées : l'origine est `CACHE`, sa date a plus de 30 jours, et le motif précise `VIES injoignable, repli sur vieille valeur connue`. Le comptable a ainsi toutes les informations pour décider s'il prend le risque ou non.
