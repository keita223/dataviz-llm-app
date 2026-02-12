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

        prompt = f"""Tu es un expert Plotly en data visualization. Génère du code Python pour créer cette visualisation.

VISUALISATION DEMANDÉE :
- Titre : {proposal['title']}
- Type : {proposal['chart_type']}
- Variables : {proposal['variables']}

COLONNES DISPONIBLES : {list(df.columns)}
TYPES DES COLONNES : {df.dtypes.astype(str).to_dict()}
NOMBRE DE LIGNES : {len(df)}
PREMIÈRES LIGNES :
{df.head(10).to_string()}

CONSIGNES STRICTES POUR UN GRAPHIQUE LISIBLE ET PROFESSIONNEL :
1. Utilise plotly.express ou plotly.graph_objects
2. Le DataFrame s'appelle 'df'
3. TITRE : clair, descriptif, taille 18px minimum
4. AXES : labels explicites (pas les noms bruts des colonnes), taille 14px
5. LÉGENDE : visible et bien positionnée
6. COULEURS : utilise une palette professionnelle (ex: px.colors.qualitative.Set2 ou plotly_white)
7. TEMPLATE : utilise template='plotly_white' pour un fond propre
8. HOVER : ajoute des infos utiles au survol (hovertemplate personnalisé si pertinent)
9. Si c'est un bar chart avec des catégories textuelles, trie les barres par valeur décroissante
10. Si les labels des axes sont longs, incline-les (tickangle=-45)
11. Ajoute des marges suffisantes : fig.update_layout(margin=dict(l=80, r=40, t=80, b=100))
12. Pour les nombres, formate-les lisiblement (ex: séparateur de milliers)
13. Si pertinent, ajoute des annotations ou des valeurs sur les barres (text_auto=True pour bar charts)

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
