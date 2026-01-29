#  DataViz LLM App

> Application web intelligente de data visualisation propulsée par un système multi-agents LLM

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

##  Description

Ce projet est développé dans le cadre du module **Data Visualization** du Master 2 BDIA (Big Data & Intelligence Artificielle) à l'Université Dauphine - PSL.

L'application permet de générer automatiquement des visualisations de données pertinentes à partir d'une problématique textuelle et d'un dataset CSV, en utilisant un système multi-agents basé sur Gemini.

##  Architecture

### Backend (FastAPI + Multi-Agents)
```
dataviz_backend/
├── agents/
│   ├── data_analyst.py      # Agent 1 : Analyse des données
│   ├── viz_strategist.py    # Agent 2 : Proposition de visualisations
│   └── code_generator.py    # Agent 3 : Génération du code Plotly
├── main.py                  # API FastAPI
├── orchestrator.py          # Coordination des agents
└── models.py                # Modèles Pydantic
```

### Frontend (React + Vite)


##  Installation

### Prérequis

- Python 3.11+
- uv (gestionnaire de paquets)
- Node.js 18+ (pour le frontend)
- Clé API Google Gemini

### Backend
```bash
# Clone le repository
git clone https://github.com/TON_USERNAME/dataviz-llm-app.git
cd dataviz-llm-app

# Installe les dépendances
uv sync

# Configure les variables d'environnement
cp .env.example .env
# Édite .env et ajoute ta clé GEMINI_API_KEY

# Active l'environnement virtuel
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# Lance le serveur
python -m uvicorn dataviz_backend.main:app --reload
```

L'API est accessible sur http://127.0.0.1:8000

Documentation interactive : http://127.0.0.1:8000/docs

### Frontend


##  Fonctionnalités

-  Upload de fichiers CSV
-  Analyse automatique des données via LLM
-  Proposition de 3 visualisations pertinentes
-  Génération automatique du graphique Plotly
-  Export en PNG
-  Respect des bonnes pratiques de data visualization

## Système Multi-Agents

1. **Data Analyst Agent** : Analyse le dataset et comprend la problématique
2. **Viz Strategist Agent** : Propose 3 visualisations adaptées
3. **Code Generator Agent** : Génère le code Plotly pour la visualisation choisie

##  Tests
```bash
pytest tests/
```

##  Stack Technique

**Backend :**
- FastAPI
- Google Gemini API
- Plotly
- Pandas
- Pydantic
- uv

**Frontend :**
- React
- Vite
- react-plotly.js
- Tailwind CSS

##  Contributeurs

- [Mamadi Keita](https://github.com/keita223)
- [Linda Ben Rajab](https://github.com/Lindabenrajab)
- [Skander Adam Afi](https://github.com/skan652)

**Reviewer :** [Hadrien Mariaccia](https://github.com/brash6) - Enseignant

##  License

MIT License - voir le fichier [LICENSE](LICENSE)

##  Projet Académique

Projet réalisé dans le cadre du cours de Data Visualization - Master 2 BDIA
Université Paris Dauphine - PSL
