import pandas as pd
import anthropic
from io import StringIO
import json
import gc

class DataAnalystAgent:
    """Agent 1 : Analyse les données et comprend la problématique"""

    MAX_ROWS_ANALYSIS = 5000  # Echantillonner si plus de 5000 lignes

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-3-haiku-20240307"

    async def analyze(self, csv_data: str, problem: str) -> dict:
        """
        Analyse le dataset et retourne un résumé structuré
        """
        # Parse CSV
        df = pd.read_csv(StringIO(csv_data))
        total_rows = len(df)

        # Echantillonner si trop gros (economie de memoire)
        if total_rows > self.MAX_ROWS_ANALYSIS:
            df = df.sample(self.MAX_ROWS_ANALYSIS, random_state=42)

        # Supprimer les colonnes Unnamed
        unnamed_cols = [c for c in df.columns if 'Unnamed' in str(c)]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)

        # Statistiques de base - SEULEMENT sur colonnes numériques
        numeric_cols = df.select_dtypes(include='number')
        column_types = df.dtypes.astype(str).to_dict()

        # Stats simplifiees (pas tout describe() qui est lourd)
        numeric_stats = {}
        for col in numeric_cols.columns[:10]:  # Max 10 colonnes
            numeric_stats[col] = {
                "mean": round(float(numeric_cols[col].mean()), 2),
                "min": round(float(numeric_cols[col].min()), 2),
                "max": round(float(numeric_cols[col].max()), 2),
            }

        # Corrélations - limiter aux 8 premieres colonnes numeriques
        correlations = None
        num_cols_list = numeric_cols.columns.tolist()[:8]
        if len(num_cols_list) > 1:
            correlations = numeric_cols[num_cols_list].corr().round(2).to_dict()

        # Contexte pour Claude (apercu limite)
        context = f"""
Dataset Information:
- Nombre de lignes : {total_rows}
- Colonnes : {list(df.columns)}
- Types : {column_types}
- Premières lignes :
{df.head(5).to_string()}

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
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            analysis = {
                "insights": response_text,
                "relevant_columns": list(df.columns),
                "recommended_approach": "Analyse exploratoire"
            }

        result = {
            "column_types": column_types,
            "numeric_stats": numeric_stats,
            "correlations": correlations,
            "insights": analysis.get("insights", ""),
            "relevant_columns": analysis.get("relevant_columns", []),
            "recommended_approach": analysis.get("recommended_approach", "")
        }

        # Liberer la memoire
        del df, numeric_cols
        gc.collect()

        return result
