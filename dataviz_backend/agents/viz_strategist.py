import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

class VizStrategistAgent:
    """Agent 2 : Propose 3 visualisations pertinentes"""
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-flash-latest')
    
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

IMPORTANT : Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.
"""
        
        response = self.model.generate_content(prompt)
        
        try:
            # Nettoie les backticks markdown si présents
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            return result.get("proposals", [])
            
        except json.JSONDecodeError:
            # Fallback : 3 propositions intelligentes par défaut
            relevant_cols = data_summary.get('relevant_columns', list(data_summary.get('column_types', {}).keys()))
            numeric_cols = [col for col, dtype in data_summary.get('column_types', {}).items() 
                            if 'int' in dtype or 'float' in dtype]
            categorical_cols = [col for col, dtype in data_summary.get('column_types', {}).items() 
                               if 'object' in dtype or 'str' in dtype]
            
            proposals = []
            
            # Proposition 1 : Scatter ou bar selon les colonnes
            if len(numeric_cols) >= 2:
                proposals.append({
                    "title": f"Relation entre {numeric_cols[0]} et {numeric_cols[1]}",
                    "chart_type": "scatter",
                    "variables": numeric_cols[:2],
                    "justification": "Analyse de la corrélation entre deux variables numériques",
                    "best_practices": "Scatter plot optimal pour visualiser les relations entre variables continues"
                })
            elif len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                proposals.append({
                    "title": f"{numeric_cols[0]} par {categorical_cols[0]}",
                    "chart_type": "bar",
                    "variables": [categorical_cols[0], numeric_cols[0]],
                    "justification": "Comparaison des valeurs numériques par catégorie",
                    "best_practices": "Bar chart clair pour comparer les catégories"
                })
            else:
                proposals.append({
                    "title": "Vue d'ensemble des données",
                    "chart_type": "bar",
                    "variables": relevant_cols[:2] if len(relevant_cols) >= 2 else relevant_cols,
                    "justification": "Comparaison générale des données",
                    "best_practices": "Visualisation simple et efficace"
                })
            
            # Proposition 2 : Histogram si colonnes numériques
            if len(numeric_cols) >= 1:
                proposals.append({
                    "title": f"Distribution de {numeric_cols[0]}",
                    "chart_type": "histogram",
                    "variables": [numeric_cols[0]],
                    "justification": "Visualisation de la distribution des valeurs pour identifier patterns et outliers",
                    "best_practices": "Histogram adapté pour comprendre la répartition des données"
                })
            else:
                proposals.append({
                    "title": "Répartition des catégories",
                    "chart_type": "bar",
                    "variables": [categorical_cols[0]] if categorical_cols else relevant_cols[:1],
                    "justification": "Visualisation de la fréquence des catégories",
                    "best_practices": "Bar chart simple pour les données catégorielles"
                })
            
            # Proposition 3 : Box plot ou autre agrégation
            if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                proposals.append({
                    "title": f"Distribution de {numeric_cols[0]} par {categorical_cols[0]}",
                    "chart_type": "box",
                    "variables": [categorical_cols[0], numeric_cols[0]],
                    "justification": "Comparaison des distributions entre catégories pour détecter variations",
                    "best_practices": "Box plot efficace pour comparer distributions et identifier outliers"
                })
            elif len(numeric_cols) >= 2:
                proposals.append({
                    "title": f"Vue croisée {numeric_cols[0]} vs {numeric_cols[1]}",
                    "chart_type": "line",
                    "variables": numeric_cols[:2],
                    "justification": "Analyse de l'évolution entre deux variables",
                    "best_practices": "Line chart pour visualiser tendances"
                })
            else:
                proposals.append({
                    "title": "Synthèse générale",
                    "chart_type": "bar",
                    "variables": relevant_cols[:2] if len(relevant_cols) >= 2 else relevant_cols,
                    "justification": "Vue globale des principales variables",
                    "best_practices": "Visualisation synthétique et accessible"
                })
            
            return proposals