# 🇪🇺 API TVA Meridian - Guide de Déploiement et de Test

Service complet de nettoyage, validation et consultation de numéros de TVA Intracommunautaires.

**Auteur:** Jean-Thomas Miquelot / Assistant IA

---

## 🛠️ Prérequis
- `uv` installé (gestionnaire de paquets Python ultra-rapide)
- Docker & Docker Compose installés (pour la base de données PostgreSQL)
- Ports `5435` (PostgreSQL) et `8000` (API) libres sur votre machine.

---

## 🚀 1. Lancement depuis zéro (Installation)

**1. Démarrer la base de données PostgreSQL via Docker :**
```bash
docker compose up -d
```

**2. Synchroniser l'environnement et initialiser les tables de la base :**
```bash
uv sync
uv run python -m src.api_tva_meridian.init_db
```

*(La base de données est maintenant prête, vide, avec son schéma construit).*

---

## 🧪 2. Tester le Pipeline (Étape par Étape)

### Étape A : Chargement et Normalisation (Phase 1)
Nous allons ingérer les 10 000 lignes brutes du fichier CSV, les nettoyer, et appliquer la validation structurelle de base sans faire d'appel réseau.
```bash
uv run python -m src.api_tva_meridian.load numeros_tva.csv
```
*(Remarque : L'opération est idempotente. Si vous la relancez, elle ne créera pas de doublons).*

### Étape B : Campagne de vérification VIES (Phase 2)
Nous allons maintenant vérifier un échantillon de ces numéros auprès du service européen officiel VIES.
```bash
# Vérifie un échantillon de 10 numéros avec un délai de 0.5 secondes entre chaque appel
uv run python -m src.api_tva_meridian.check_campaign --sample 10 --delay 0.5
```
**Crash test de reprise :** 
1. Lancez la commande pour un gros échantillon (ex: `--sample 200`).
2. Faites un `CTRL+C` au bout de 5 vérifications pour l'interrompre.
3. Relancez la commande. Vous constaterez que le script reprend intelligemment là où il s'était arrêté, ignorant les numéros déjà validés.

### Étape C : Générer le Rapport de Réconciliation
Pour prouver à la direction financière l'état du référentiel et la réduction drastique du nombre d'appels réseau (grâce à la déduplication et à la validation structurelle).
```bash
uv run python -m src.api_tva_meridian.report
```

---

## 🌐 3. Tester l'API REST (Temps Réel)

L'API est destinée à être appelée par la facturation avant d'émettre une facture HT.

**1. Démarrer le serveur API :**
```bash
uv run uvicorn src.api_tva_meridian.main:app --host 0.0.0.0 --port 8000
```

**2. Tests d'appels depuis un autre terminal (ou via le navigateur) :**

- **Documentation Swagger / Interface de test UI :**  
  👉 Ouvrez votre navigateur sur : [http://localhost:8000/docs](http://localhost:8000/docs)

- **Test en ligne de commande (cURL) :**

  *Cas 1 : Un numéro structurellement invalide (renvoie instantanément INVALIDE sans réseau)*
  ```bash
  curl "http://localhost:8000/validate/FR/55423851084"
  ```

  *Cas 2 : Un numéro valide en cache (fraîcheur locale)*
  *(Si vous venez de lancer la campagne VIES, copiez un numéro valide dans les logs et testez-le)*
  ```bash
  curl "http://localhost:8000/validate/DK/47458714"
  ```

---

## 📚 En Savoir Plus
- 📖 [Lisez EXPLICATIONS_DETAILLES.md](./EXPLICATIONS_DETAILLES.md) pour comprendre comment fonctionnent la normalisation, la réduction d'appels et la gestion de VIES point par point.
- 🏗️ Lisez `ARCHITECTURE.md` pour les décisions de conception.
- 📓 Lisez `JOURNAL.md` pour le récit de la construction.
