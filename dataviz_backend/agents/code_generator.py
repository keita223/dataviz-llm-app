import anthropic
import pandas as pd
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
import json

class CodeGeneratorAgent:
    """Agent 3 : Génère le code Plotly pour la visualisation choisie"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-3-haiku-20240307"

    async def generate_visualization(self, proposal: dict, csv_data: str) -> dict:
        """
        Génère le code Plotly et retourne le JSON du graphique
        """
        df = pd.read_csv(StringIO(csv_data))

        prompt = f"""Tu es un expert Plotly. Génère du code Python pour créer cette visualisation.

VISUALISATION DEMANDÉE :
- Titre : {proposal['title']}
- Type : {proposal['chart_type']}
- Variables : {proposal['variables']}

COLONNES DISPONIBLES : {list(df.columns)}
PREMIÈRES LIGNES :
{df.head().to_string()}

CONSIGNES :
1. Utilise plotly.express ou plotly.graph_objects
2. Code propre et commenté
3. Titre, axes, légendes bien formatés
4. Couleurs professionnelles
5. Le DataFrame s'appelle 'df'

Réponds avec un code Python exécutable, SANS ```python et SANS texte explicatif.
Juste le code pur qui crée une variable 'fig'.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text.strip()

        # Nettoie le code (enlève markdown si présent)
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        # Exécute le code pour générer la figure
        try:
            local_scope = {"df": df, "px": px, "go": go, "pd": pd}
            exec(code, local_scope)
            fig = local_scope.get('fig')

            if fig is None:
                raise ValueError("Le code n'a pas créé de variable 'fig'")

            return {
                "plotly_json": json.loads(fig.to_json()),
                "code": code
            }
        except Exception as e:
            # Fallback : graphique simple
            fig = px.scatter(df, x=df.columns[0], y=df.columns[1] if len(df.columns) > 1 else df.columns[0],
                           title=proposal['title'])
            return {
                "plotly_json": json.loads(fig.to_json()),
                "code": f"# Erreur lors de la génération : {str(e)}\n{code}"
            }
