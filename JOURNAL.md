# Journal de Bord

## Phase 1 : Normalisation et validation
- **Observation du jeu de données :** Le jeu contenait beaucoup de bruit de saisie, notamment des valeurs NaN/NULL qui devaient être identifiées (146 valeurs vides dissimulées). De plus, certaines confusions entre lettres (O/I) et chiffres (0/1) rendaient des numéros invalides alors qu'ils étaient potentiellement bons.
- **Résolution :** Modification de `normalize.py` pour traiter explicitement les variantes textuelles de NULL comme des valeurs vides `VIDE_OU_NUL`. Pour le bruit OCR (O/0, I/1), j'ai rajouté un fallback dans la vérification de la clé de contrôle de `stdnum` : en cas d'échec initial, si une correction basique permet une validation stricte, le numéro est requalifié en "VALIDE".
- **Chargement en base :** Le script de chargement gère nativement les doublons via une clause `ON CONFLICT DO UPDATE`, ce qui rend le rechargement idempotent.

## Phase 2 : Connexion à VIES
- **Blocage technique :** Ma première tentative d'utiliser le client interne `vat.check_vies()` de `python-stdnum` a échoué car il dépendait d'une librairie SOAP `zeep` non fournie ni autorisée d'office. De plus, j'ai eu des Timeouts sur mes premières requêtes REST directes à cause de lenteurs VIES.
- **Résolution :** J'ai implémenté un client direct sur l'API REST officielle récente (`/rest-api/check-vat-number`) en utilisant `httpx` avec un timeout de 15 secondes. L'API REST s'est avérée fiable.
- **Cas particulier :** L'API VIES renvoie parfois des `MS_MAX_CONCURRENT_REQ`. Ces erreurs de limitation technique sont consciencieusement capturées, analysées depuis le payload JSON et qualifiées en `INDETERMINE`.
- **API Locale :** Pour la création de l'API locale avec FastAPI, j'ai introduit la notion de "fraîcheur". Plutôt que de stocker et d'oublier, le contrat d'API gère un repli intelligent en cas de dysfonctionnement passager de VIES.
