# API TVA Meridian

Service de nettoyage, validation et consultation de numéros de TVA Intracommunautaires pour la société Meridian Distribution.

**Auteur:** Jean-Thomas Miquelot / Assistant IA

## Description
Ce projet répond au besoin de Meridian Distribution de valider une base de 10 000 numéros de TVA clients, dans un contexte d'autoliquidation de la TVA à l'international. 
Il propose un pipeline de données complet :
1. **Import et normalisation** des numéros bruts depuis un fichier d'origine.
2. **Filtrage structurel** sans appel réseau, pour écarter rapidement les erreurs de format (et corriger automatiquement les bruits de saisie basiques).
3. **Campagne de validation en ligne (VIES)** en mode différé, hautement tolérante aux interruptions.
4. **Exposition via API REST**, pour permettre au service de facturation de vérifier un numéro en temps réel avant d'émettre une facture HT.

## Technologies & Justification
- **Python 3.12+** & **uv** : Écosystème rapide et moderne.
- **FastAPI** : Choix idéal pour construire l'API REST : rapide, typé statiquement via Pydantic, et générant automatiquement la documentation OpenAPI.
- **PostgreSQL** : Base de données robuste pour stocker l'historique et les différents états des verdicts (brut, structurel, en ligne).
- **SQLAlchemy** : ORM standard facilitant les interactions avec PostgreSQL.
- **pandas** : Simplifie la manipulation et le nettoyage initial du fichier source (CSV/Excel).
- **python-stdnum** : Bibliothèque robuste pour la validation structurelle et la clé de contrôle des numéros de TVA (pour éviter de réécrire les regex des 27 pays de l'UE).
- **httpx** : Client HTTP moderne pour effectuer les appels vers l'API REST VIES.

## Lancement depuis zéro

### 1. Prérequis
- Python 3.12+ (ou l'outil `uv` installé)
- Docker & Docker Compose
- Le port `5435` disponible pour PostgreSQL et le port `8000` pour l'API.

### 2. Démarrage de la base de données
```bash
docker compose up -d
```

### 3. Installation et initialisation
Exécutez ce qui suit pour préparer l'environnement et construire les tables :
```bash
uv sync
uv run python -m src.api_tva_meridian.init_db
```

### 4. Chargement et Normalisation (Phase 1)
Chargez les données du fichier dans la base. Cette étape effectue également la validation structurelle.
```bash
uv run python -m src.api_tva_meridian.load numeros_tva.csv
```

### 5. Campagne de vérification VIES (Phase 2)
Vous pouvez lancer une campagne sur un échantillon pour vérifier les appels VIES (avec temporisation).
```bash
# Vérifier 200 numéros, avec 1 seconde d'écart
uv run python -m src.api_tva_meridian.check_campaign --sample 200 --delay 1.0
```
*Le script est interruptible et reprendra là où il s'est arrêté lors d'une relance.*

### 6. Rapport de réconciliation
Générez l'état des lieux pour la direction financière :
```bash
uv run python -m src.api_tva_meridian.report
```

### 7. Démarrage de l'API
Démarrez le serveur FastAPI :
```bash
uv run uvicorn src.api_tva_meridian.main:app --host 0.0.0.0 --port 8000
```
La documentation Swagger est accessible sur : `http://localhost:8000/docs`.

Pour tester, depuis un autre terminal :
```bash
curl "http://localhost:8000/validate/FR/55423851084"
```
