import pandas as pd
import google.generativeai as genai
from io import StringIO
import json
import os
from dotenv import load_dotenv

load_dotenv()

class DataAnalystAgent:
    """Agent 1 : Analyse les données et comprend la problématique"""
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-flash-latest')
    
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
        
        # Contexte pour Gemini
        context = f"""
Dataset Information:
- Nombre de lignes : {len(df)}
- Colonnes : {list(df.columns)}
- Types : {column_types}
- Premières lignes :
{df.head(10).to_string()}

Problématique utilisateur : {problem}
"""
        
        # Prompt pour Gemini
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
        
        response = self.model.generate_content(prompt)
        
        try:
            # Nettoie les backticks markdown si présents
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # Parse la réponse JSON
            analysis = json.loads(text)
        except json.JSONDecodeError:
            # Fallback si Gemini ne retourne pas du JSON pur
            analysis = {
                "insights": response.text,
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