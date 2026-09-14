# Note d'Architecture

## Réduction des appels à VIES
La réduction des appels au service externe VIES est au cœur de notre stratégie pour limiter la charge réseau et respecter les limitations potentielles du service gratuit de la Commission Européenne.

**Méthode :**
1. **Validation Structurelle Préalable** : Avant de considérer un appel réseau, nous testons la validité formelle et mathématique du numéro via la bibliothèque `python-stdnum`. Tous les numéros structurellement invalides sont d'emblée rejetés sans appel réseau.
2. **Déduplication stricte** : Après la normalisation, plusieurs saisies manuelles différentes aboutissent au même numéro de TVA normalisé. Nous ciblons notre requête sur l'ensemble *distinct* des numéros normalisés valides, et nous propageons ensuite le verdict en base de données sur toutes les lignes associées.

**Chiffres de réduction (sur le lot de 10 000 numéros) :**
- Lignes d'origine : 10 000
- Lignes structurellement valides : 5 362 (réduction de ~46% par validation stricte et nettoyage)
- Numéros uniques à vérifier parmi les valides : 5 119 (réduction supplémentaire de 243 doublons stricts)
- Appels VIES évités au total : 4 881.

## Durée de validité d'un verdict (Fraîcheur)
L'état d'un numéro de TVA n'est pas immuable (une entreprise peut fermer ou perdre son statut).
Dans l'API, nous accordons une durée de validité ("fraîcheur") de **30 jours** à un verdict VIES en cache.
- Si la facturation interroge un numéro dont la vérification date de moins de 30 jours, nous renvoyons le résultat du cache.
- Si le résultat a plus de 30 jours, nous tentons un nouvel appel VIES transparent pour l'appelant.

Ce délai de 30 jours offre un compromis acceptable entre sécurité fiscale (limiter le risque de fausses validations) et robustesse (éviter la surcharge réseau systématique à chaque facture).

## Gestion des Indéterminés
Les "Indéterminés" regroupent les cas où VIES ne peut pas nous répondre formellement (Service Unavailable, Timeout réseau, Max Concurrent Requests).
- **Lors de la campagne de batch** : L'état `INDETERMINE` est sauvegardé en base sans écraser d'anciennes valeurs réelles. Les requêtes de relance intègrent la condition de reprendre les `INDETERMINE` pour retenter le coup plus tard.
- **Lors de l'appel API (temps réel)** : 
  - Si l'API VIES échoue, nous tentons de retomber sur la dernière valeur connue en cache (même si elle est périmée de plus de 30 jours), afin de ne pas bloquer l'émission de la facture si nous étions précédemment confiants.
  - S'il n'y a aucune donnée en cache et que VIES est en carafe, nous retournons `INDETERMINE`. Le client (la facturation) devra suspendre l'autoliquidation ou alerter un comptable humain. En aucun cas une erreur technique n'est renvoyée comme "Invalide".
