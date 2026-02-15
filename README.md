# DataViz LLM App

> Application web intelligente de data visualisation propulsee par un systeme multi-agents LLM

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Description

Projet developpe dans le cadre du module **Data Visualization** du Master 2 BDIA (Big Data & Intelligence Artificielle) a l'Universite Paris Dauphine - PSL.

L'application permet de generer automatiquement des visualisations de donnees pertinentes a partir d'une problematique textuelle et d'un dataset CSV, en utilisant un systeme multi-agents base sur **Claude (Anthropic)**.

## Lien vers l'application deployee

**https://dataviz-llm-app-production.up.railway.app**

## Architecture

```
dataviz-llm-app/
├── dataviz_backend/
│   ├── agents/
│   │   ├── data_analyst.py       # Agent 1 : Analyse des donnees
│   │   ├── viz_strategist.py     # Agent 2 : Proposition de visualisations
│   │   └── code_generator.py     # Agent 3 : Generation du code matplotlib
│   ├── main.py                   # API FastAPI + serveur frontend
│   ├── orchestrator.py           # Coordination des 3 agents
│   └── models.py                 # Modeles Pydantic
├── dataviz_front/
│   ├── index.html                # Interface utilisateur (HTML + JS inline)
│   └── style.css                 # Styles CSS
├── tests/
│   ├── test_api.py               # Tests des endpoints API
│   └── test_agents.py            # Tests des agents
├── pyproject.toml                # Configuration projet (uv)
├── requirements.txt              # Dependances Python
├── Dockerfile                    # Configuration Docker
├── Procfile                      # Configuration Railway
└── README.md
```

## Systeme Multi-Agents

L'application utilise 3 agents LLM specialises, orchestres sequentiellement :

1. **Data Analyst Agent** : Analyse le dataset CSV et comprend la problematique de l'utilisateur. Retourne un resume structure (insights, colonnes pertinentes, approche recommandee).

2. **Viz Strategist Agent** : Propose exactement 3 visualisations differentes (types de graphiques distincts), chacune justifiee par rapport a la problematique et conforme aux bonnes pratiques de data visualization.

3. **Code Generator Agent** : Genere du code Python (matplotlib/seaborn) via le LLM, l'execute cote serveur, et retourne l'image en base64. Inclut un mecanisme de retry (3 tentatives) et un fallback deterministe.

## Installation

### Prerequisites

- Python 3.11+
- uv (gestionnaire de paquets)
- Cle API Anthropic (Claude)

### Setup

```bash
# Cloner le repository
git clone https://github.com/keita223/dataviz-llm-app.git
cd dataviz-llm-app

# Installer les dependances avec uv
uv sync

# Ou avec pip
pip install -r requirements.txt

# Configurer la cle API
cp .env.example .env
# Editer .env et ajouter : ANTHROPIC_API_KEY=sk-ant-...

# Activer l'environnement virtuel
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\Activate.ps1   # Windows
```

### Lancement

```bash
python -m uvicorn dataviz_backend.main:app --reload
```

L'application est accessible sur http://127.0.0.1:8000

Documentation API interactive : http://127.0.0.1:8000/docs

## Fonctionnalites

- Upload de fichiers CSV avec drag & drop
- Analyse automatique des donnees via LLM (Claude Haiku)
- Proposition de 3 visualisations pertinentes avec types differents
- Generation automatique du graphique matplotlib/seaborn
- Affichage du code Python genere (transparence)
- Export / telechargement en PNG
- Respect des bonnes pratiques de data visualization (lisibilite, data-ink ratio, absence de chartjunk)

## Tests

```bash
# Installer les dependances de test
pip install pytest pytest-asyncio httpx

# Lancer les tests
pytest tests/ -v
```

## Stack Technique

- **Backend** : FastAPI, Python 3.11+
- **LLM** : Claude Haiku (Anthropic API)
- **Visualisation** : matplotlib, seaborn
- **Frontend** : HTML/CSS/JS vanilla (servi par FastAPI)
- **Deploiement** : Railway (Docker)
- **Gestionnaire de paquets** : uv

## Contributeurs

- [Mamadi Keita](https://github.com/keita223)
- [Linda Ben Rajab](https://github.com/Lindabenrajab)
- [Skander Afi](https://github.com/skan652)

**Reviewer** : Hadrien Mariaccia - Enseignant

## License

MIT License - voir le fichier [LICENSE](LICENSE)

## Projet Academique

Projet realise dans le cadre du cours de Data Visualization - Master 2 BDIA
Universite Paris Dauphine - PSL
