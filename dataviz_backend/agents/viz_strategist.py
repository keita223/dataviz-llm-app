import google.genai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

class VizStrategistAgent:
    """Agent 2 : Propose 3 visualisations pertinentes"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    async def propose_visualizations(self, data_summary: dict, problem: str) -> list:
        """
        Génère 3 propositions de visualisations différentes
        """
        
        prompt = f"""Tu es un expert en data visualization. 

CONTEXTE :
Problématique : {problem}

Analyse des données :
- Colonnes pertinentes : {data_summary.get('relevant_columns', [])}
- Types de colonnes : {data_summary.get('column_types', {})}
- Insights : {data_summary.get('insights', '')}
- Approche recommandée : {data_summary.get('recommended_approach', '')}

BONNES PRATIQUES À RESPECTER :
- Choisir le type de graphique adapté (scatter pour corrélation, bar pour comparaison, box pour distribution, etc.)
- Maximiser le data-ink ratio (pas de chartjunk)
- Utiliser des couleurs appropriées et accessibles
- Axes et légendes clairs
- Titre explicite

TÂCHE :
Propose EXACTEMENT 3 visualisations DIFFÉRENTES qui répondent à la problématique.
Chaque visualisation doit respecter les bonnes pratiques vues en cours.

Réponds en JSON avec cette structure EXACTE :
{{
    "proposals": [
        {{
            "title": "Titre explicite de la visualisation",
            "chart_type": "scatter|bar|box|heatmap|line|histogram",
            "variables": ["colonne_x", "colonne_y"],
            "justification": "Pourquoi cette visualisation répond à la problématique",
            "best_practices": "Comment elle respecte les bonnes pratiques (data-ink ratio, choix du type, etc.)"
        }},
        ... (2 autres propositions DIFFÉRENTES)
    ]
}}

IMPORTANT : Réponds UNIQUEMENT avec le JSON, rien d'autre.
"""
        
        response = self.client.models.generate_content(
    model='gemini-1.5-pro',
    contents=prompt
)
        
        try:
            result = json.loads(response.text.strip())
            return result.get("proposals", [])
        except json.JSONDecodeError:
            # Fallback : propositions par défaut
            return [
                {
                    "title": "Proposition par défaut 1",
                    "chart_type": "scatter",
                    "variables": data_summary.get('relevant_columns', [])[:2],
                    "justification": "Analyse de corrélation",
                    "best_practices": "Scatter plot optimal pour voir les relations"
                }
            ]