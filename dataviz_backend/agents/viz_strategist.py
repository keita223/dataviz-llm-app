import anthropic
import json

class VizStrategistAgent:
    """Agent 2 : Propose 3 visualisations pertinentes"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-3-haiku-20240307"

    async def propose_visualizations(self, data_summary: dict, problem: str) -> list:
        """
        Génère 3 propositions de visualisations différentes
        """

        # Extraire les colonnes par type
        column_types = data_summary.get('column_types', {})
        numeric_cols = [c for c, t in column_types.items() if 'int' in t or 'float' in t]
        categorical_cols = [c for c, t in column_types.items() if 'object' in t or 'category' in t]

        prompt = f"""Tu es un expert en data visualization.

CONTEXTE :
Problématique : {problem}

Analyse des données :
- Colonnes pertinentes : {data_summary.get('relevant_columns', [])}
- Colonnes numériques : {numeric_cols}
- Colonnes catégorielles : {categorical_cols}
- Insights : {data_summary.get('insights', '')}
- Approche recommandée : {data_summary.get('recommended_approach', '')}

TÂCHE :
Propose EXACTEMENT 3 visualisations qui répondent à la problématique.

RÈGLES STRICTES :
1. Chaque proposition doit utiliser un chart_type DIFFÉRENT. Par exemple : une bar, une scatter, une pie. JAMAIS 2 fois le même type.
2. Les variables doivent être des noms de colonnes qui EXISTENT dans les données ci-dessus.
3. Pour les variables, utilise les colonnes catégorielles en x et numériques en y.
4. Types autorisés : bar, scatter, pie, box, line, histogram, heatmap

Réponds en JSON avec cette structure EXACTE :
{{
    "proposals": [
        {{
            "title": "Titre explicite",
            "chart_type": "bar",
            "variables": ["colonne_x", "colonne_y"],
            "justification": "Pourquoi cette visualisation",
            "best_practices": "Bonnes pratiques respectées"
        }},
        {{
            "title": "Titre explicite",
            "chart_type": "scatter",
            "variables": ["colonne_x", "colonne_y"],
            "justification": "Pourquoi cette visualisation",
            "best_practices": "Bonnes pratiques respectées"
        }},
        {{
            "title": "Titre explicite",
            "chart_type": "pie",
            "variables": ["colonne_x", "colonne_y"],
            "justification": "Pourquoi cette visualisation",
            "best_practices": "Bonnes pratiques respectées"
        }}
    ]
}}

IMPORTANT : Les 3 chart_type DOIVENT être différents. Réponds UNIQUEMENT avec le JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        try:
            result = json.loads(response_text.strip())
            proposals = result.get("proposals", [])

            # Vérifier que les 3 types sont différents
            seen_types = set()
            unique_proposals = []
            for p in proposals:
                chart_type = p.get('chart_type', '').lower()
                if chart_type not in seen_types:
                    seen_types.add(chart_type)
                    unique_proposals.append(p)

            # Si des doublons ont été retirés, compléter avec des types manquants
            if len(unique_proposals) < 3:
                all_types = ['bar', 'scatter', 'pie', 'box', 'histogram', 'line']
                relevant_cols = data_summary.get('relevant_columns', [])
                for t in all_types:
                    if t not in seen_types and len(unique_proposals) < 3:
                        unique_proposals.append({
                            "title": f"Analyse par {t} chart",
                            "chart_type": t,
                            "variables": relevant_cols[:2],
                            "justification": "Visualisation complémentaire",
                            "best_practices": "Type de graphique différent pour une autre perspective"
                        })
                        seen_types.add(t)

            return unique_proposals[:3]

        except json.JSONDecodeError:
            relevant_cols = data_summary.get('relevant_columns', [])
            return [
                {
                    "title": "Comparaison par catégorie",
                    "chart_type": "bar",
                    "variables": relevant_cols[:2],
                    "justification": "Bar chart pour comparer les valeurs",
                    "best_practices": "Comparaison visuelle claire"
                },
                {
                    "title": "Corrélation entre variables",
                    "chart_type": "scatter",
                    "variables": relevant_cols[:2],
                    "justification": "Scatter plot pour voir les relations",
                    "best_practices": "Identification de patterns"
                },
                {
                    "title": "Répartition des données",
                    "chart_type": "pie",
                    "variables": relevant_cols[:2],
                    "justification": "Pie chart pour voir les proportions",
                    "best_practices": "Vue d'ensemble des proportions"
                }
            ]
