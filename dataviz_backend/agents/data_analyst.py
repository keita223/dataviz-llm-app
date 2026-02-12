import pandas as pd
import anthropic
from io import StringIO
import json

class DataAnalystAgent:
    """Agent 1 : Analyse les données et comprend la problématique"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-3-haiku-20240307"

    async def analyze(self, csv_data: str, problem: str) -> dict:
        """
        Analyse le dataset et retourne un résumé structuré
        """
        # Parse CSV
        df = pd.read_csv(StringIO(csv_data))

        # Statistiques de base - SEULEMENT sur colonnes numériques
        numeric_cols = df.select_dtypes(include='number')
        column_types = df.dtypes.astype(str).to_dict()
        numeric_stats = numeric_cols.describe().to_dict() if len(numeric_cols.columns) > 0 else {}

        # Corrélations - SEULEMENT sur colonnes numériques
        correlations = None
        if len(numeric_cols.columns) > 1:
            correlations = numeric_cols.corr().to_dict()

        # Contexte pour Claude
        context = f"""
Dataset Information:
- Nombre de lignes : {len(df)}
- Colonnes : {list(df.columns)}
- Types : {column_types}
- Premières lignes :
{df.head(10).to_string()}

Problématique utilisateur : {problem}
"""

        # Prompt pour Claude
        prompt = f"""Tu es un data analyst expert. Analyse ce dataset et cette problématique.

{context}

Fournis une analyse structurée en JSON avec cette structure exacte :
{{
    "insights": "Description des patterns clés, valeurs manquantes, distributions importantes",
    "relevant_columns": ["colonne1", "colonne2"],
    "recommended_approach": "Approche analytique recommandée pour répondre à la problématique"
}}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        try:
            # Parse la réponse JSON
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            # Fallback si Claude ne retourne pas du JSON pur
            analysis = {
                "insights": response_text,
                "relevant_columns": list(df.columns),
                "recommended_approach": "Analyse exploratoire"
            }

        return {
            "column_types": column_types,
            "numeric_stats": numeric_stats,
            "correlations": correlations,
            "insights": analysis.get("insights", ""),
            "relevant_columns": analysis.get("relevant_columns", []),
            "recommended_approach": analysis.get("recommended_approach", "")
        }
