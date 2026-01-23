import google.generativeai as genai
import pandas as pd
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from dotenv import load_dotenv

load_dotenv()

class CodeGeneratorAgent:
    """Agent 3 : Génère le code Plotly pour la visualisation choisie"""

    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-flash-latest")

    async def generate_visualization(self, proposal: dict, csv_data: str) -> dict:
        """
        Génère le code Plotly et retourne le JSON du graphique
        """

        # Lecture du CSV
        df = pd.read_csv(StringIO(csv_data))

        # Sécurité : forcer les colonnes numériques quand possible
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="ignore")

        prompt = f"""Tu es un expert Plotly. Génère du code Python pour créer cette visualisation.

VISUALISATION DEMANDÉE :
- Titre : {proposal['title']}
- Type : {proposal['chart_type']}
- Variables : {proposal['variables']}

COLONNES DISPONIBLES : {list(df.columns)}
TYPES DES COLONNES : {df.dtypes.to_dict()}
PREMIÈRES LIGNES :
{df.head().to_string()}

CONSIGNES STRICTES :
1. Utilise plotly.express (px) de préférence
2. Le DataFrame s'appelle EXACTEMENT 'df'
3. Le code DOIT créer une variable 'fig'
4. Titre, axes et légendes bien formatés
5. Couleurs professionnelles
6. Si price et sales existent, tu peux calculer revenue = price * sales

Réponds avec un code Python exécutable, SANS ```python et SANS texte explicatif.
Juste le code pur qui crée la variable 'fig'.
"""

        response = self.model.generate_content(prompt)
        code = response.text.strip()

        # Nettoyage amélioré du markdown
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            # Enlève tous les backticks
            parts = code.split("```")
            # Prend la partie qui contient du code (généralement la 2ème partie)
            code = parts[1].strip() if len(parts) > 1 else code
        
        try:
            # Exécution sécurisée du code généré
            local_scope = {
                "df": df,
                "px": px,
                "go": go,
                "pd": pd
            }

            exec(code, local_scope)
            fig = local_scope.get("fig")

            # Validation forte du graphique
            if fig is None or not hasattr(fig, "data") or len(fig.data) == 0:
                raise ValueError("Figure Plotly vide ou invalide")

            return {
                "plotly_json": json.loads(fig.to_json()),
                "code": code
            }

        except Exception as e:
            # 🔥 FALLBACK INTELLIGENT basé sur le type de chart demandé
            chart_type = proposal.get("chart_type", "bar")
            variables = proposal.get("variables", [])
            
            # Identifie les colonnes numériques et catégorielles
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            try:
                if chart_type == "scatter" and len(numeric_cols) >= 2:
                    fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=proposal['title'])
                
                elif chart_type == "bar":
                    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                        fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0], title=proposal['title'])
                    elif len(numeric_cols) >= 2:
                        fig = px.bar(df, x=df.columns[0], y=numeric_cols[0], title=proposal['title'])
                    else:
                        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=proposal['title'])
                
                elif chart_type == "histogram" and len(numeric_cols) >= 1:
                    fig = px.histogram(df, x=numeric_cols[0], title=proposal['title'])
                
                elif chart_type == "box":
                    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                        fig = px.box(df, x=categorical_cols[0], y=numeric_cols[0], title=proposal['title'])
                    else:
                        fig = px.box(df, y=numeric_cols[0] if numeric_cols else df.columns[0], title=proposal['title'])
                
                elif chart_type == "line" and len(numeric_cols) >= 2:
                    fig = px.line(df, x=numeric_cols[0], y=numeric_cols[1], title=proposal['title'])
                
                else:
                    # Fallback ultime : bar chart simple
                    fig = px.bar(df, x=df.columns[0], y=df.columns[1] if len(df.columns) > 1 else df.columns[0], 
                               title=proposal['title'])
                
                return {
                    "plotly_json": json.loads(fig.to_json()),
                    "code": f"# Fallback utilisé (erreur: {str(e)})\n{code}"
                }
            
            except Exception as fallback_error:
                # Fallback ultime si tout échoue
                fig = px.bar(df, x=df.columns[0], y=df.columns[1] if len(df.columns) > 1 else df.columns[0],
                           title="Visualisation générique")
                
                return {
                    "plotly_json": json.loads(fig.to_json()),
                    "code": f"# Double fallback\n# Erreur originale: {str(e)}\n# Erreur fallback: {str(fallback_error)}"
                }