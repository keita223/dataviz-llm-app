import anthropic
import pandas as pd
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np


class CodeGeneratorAgent:
    """Agent 3 : Génère le code Plotly pour la visualisation choisie"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-3-haiku-20240307"

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie le DataFrame avant utilisation"""
        # Supprimer les colonnes 'Unnamed'
        unnamed_cols = [c for c in df.columns if 'Unnamed' in str(c)]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)
        return df

    def _get_data_context(self, df: pd.DataFrame) -> str:
        """Génère un résumé clair des données pour le prompt"""
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()

        # Détecter les colonnes date en format string
        import warnings
        for col in categorical_cols[:]:
            sample = df[col].dropna().head()
            if sample.empty:
                continue
            # Vérifier si ça ressemble à une date (contient - ou /)
            first_val = str(sample.iloc[0])
            if any(sep in first_val for sep in ['-', '/']) and any(c.isdigit() for c in first_val):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        pd.to_datetime(sample)
                    date_cols.append(col)
                    categorical_cols.remove(col)
                except (ValueError, TypeError):
                    pass

        context = f"""COLONNES DISPONIBLES : {list(df.columns)}
COLONNES NUMÉRIQUES : {numeric_cols}
COLONNES CATÉGORIELLES : {categorical_cols}
COLONNES DATE : {date_cols}
NOMBRE DE LIGNES : {len(df)}
PREMIÈRES LIGNES :
{df.head(5).to_string()}"""
        return context

    def _build_prompt(self, proposal: dict, df: pd.DataFrame, error_msg: str = None) -> str:
        """Construit le prompt pour la génération de code"""
        data_context = self._get_data_context(df)

        # Vérifier que les variables demandées existent
        requested_vars = proposal.get('variables', [])
        valid_vars = [v for v in requested_vars if v in df.columns]
        invalid_vars = [v for v in requested_vars if v not in df.columns]

        vars_warning = ""
        if invalid_vars:
            vars_warning = f"\nATTENTION : Ces colonnes n'existent PAS dans le DataFrame : {invalid_vars}. Utilise uniquement les colonnes disponibles."

        retry_info = ""
        if error_msg:
            retry_info = f"""
TENTATIVE PRÉCÉDENTE ÉCHOUÉE avec cette erreur : {error_msg}
Corrige le code pour éviter cette erreur. Utilise uniquement les colonnes qui existent dans df.columns.
"""

        prompt = f"""Tu es un expert Plotly. Génère du code Python pour créer cette visualisation.

VISUALISATION :
- Titre : {proposal['title']}
- Type : {proposal['chart_type']}
- Variables souhaitées : {valid_vars if valid_vars else requested_vars}
{vars_warning}

{data_context}
{retry_info}
RÈGLES OBLIGATOIRES :
1. Utilise plotly.express (px). Le DataFrame s'appelle 'df'.
2. Utilise template='plotly_white'
3. Pour bar chart : text_auto=True. NE PAS utiliser texttemplate ni hovertemplate.
4. Pour scatter : passer les noms de colonnes en x= et y= (des strings, PAS des index).
5. Pour pie : utilise px.pie avec names= et values= (colonnes existantes).
6. Si tu dois agréger les données, fais-le avec df.groupby().sum().reset_index() ou df.value_counts().reset_index() AVANT de tracer.
7. Ajoute fig.update_layout(title_font_size=18, margin=dict(l=80, r=40, t=80, b=100))
8. Si les labels sont longs : fig.update_xaxes(tickangle=-45)
9. NE PAS utiliser texttemplate, hovertemplate, %{{text}}, ou tout format Plotly avancé.
10. Vérifie que TOUTES les colonnes que tu utilises existent dans {list(df.columns)}.

Réponds UNIQUEMENT avec du code Python exécutable.
PAS de ```python, PAS de texte, PAS de commentaires. Juste le code qui crée 'fig'."""

        return prompt

    def _clean_code(self, code: str) -> str:
        """Nettoie le code généré"""
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        # Supprimer les lignes qui ne sont pas du code
        lines = code.split('\n')
        code_lines = [l for l in lines if not l.strip().startswith(('Voici', 'Here', 'Ce code', 'This'))]
        return '\n'.join(code_lines).strip()

    def _execute_code(self, code: str, df: pd.DataFrame):
        """Exécute le code et retourne la figure"""
        local_scope = {"df": df, "px": px, "go": go, "pd": pd, "np": np}
        exec(code, local_scope)
        fig = local_scope.get('fig')
        if fig is None:
            raise ValueError("Le code n'a pas créé de variable 'fig'")
        return fig

    def _build_fallback(self, proposal: dict, df: pd.DataFrame):
        """Construit un graphique fallback intelligent basé sur le type demandé"""
        chart_type = proposal.get('chart_type', 'bar').lower()
        title = proposal.get('title', 'Visualisation')
        variables = proposal.get('variables', [])

        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Trouver les meilleures colonnes à utiliser
        x_col = None
        y_col = None

        # Essayer d'utiliser les variables demandées
        for v in variables:
            if v in df.columns:
                if v in numeric_cols and y_col is None:
                    y_col = v
                elif v in categorical_cols and x_col is None:
                    x_col = v

        # Fallback si pas trouvé
        if x_col is None and categorical_cols:
            x_col = categorical_cols[0]
        if y_col is None and numeric_cols:
            y_col = numeric_cols[0]

        if chart_type == 'pie' and x_col and y_col:
            agg_df = df.groupby(x_col)[y_col].sum().reset_index()
            fig = px.pie(agg_df, names=x_col, values=y_col, title=title, template='plotly_white')

        elif chart_type == 'scatter' and numeric_cols and len(numeric_cols) >= 2:
            col_x = numeric_cols[0]
            col_y = numeric_cols[1]
            fig = px.scatter(df, x=col_x, y=col_y, title=title, template='plotly_white')

        elif chart_type == 'histogram' and numeric_cols:
            fig = px.histogram(df, x=numeric_cols[0], title=title, template='plotly_white')

        elif chart_type == 'box' and x_col and y_col:
            fig = px.box(df, x=x_col, y=y_col, title=title, template='plotly_white')

        elif chart_type == 'line' and y_col:
            x = df.columns[0] if not x_col else x_col
            fig = px.line(df, x=x, y=y_col, title=title, template='plotly_white')

        elif chart_type == 'heatmap' and len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            fig = px.imshow(corr, text_auto=True, title=title, template='plotly_white')

        elif x_col and y_col:
            agg_df = df.groupby(x_col)[y_col].sum().reset_index()
            agg_df = agg_df.sort_values(y_col, ascending=False)
            fig = px.bar(agg_df, x=x_col, y=y_col, title=title, template='plotly_white', text_auto=True)

        else:
            # Dernier recours
            if numeric_cols:
                fig = px.histogram(df, x=numeric_cols[0], title=title, template='plotly_white')
            else:
                counts = df[df.columns[0]].value_counts().reset_index()
                counts.columns = [df.columns[0], 'count']
                fig = px.bar(counts, x=df.columns[0], y='count', title=title, template='plotly_white', text_auto=True)

        fig.update_layout(title_font_size=18, margin=dict(l=80, r=40, t=80, b=100))
        return fig

    async def generate_visualization(self, proposal: dict, csv_data: str) -> dict:
        """
        Génère le code Plotly et retourne le JSON du graphique.
        Retry automatique en cas d'erreur.
        """
        df = pd.read_csv(StringIO(csv_data))
        df = self._clean_dataframe(df)

        max_retries = 2
        last_error = None
        last_code = ""

        for attempt in range(max_retries):
            # Construire le prompt (avec erreur si retry)
            error_msg = str(last_error) if last_error else None
            prompt = self._build_prompt(proposal, df, error_msg)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            code = self._clean_code(response.content[0].text.strip())
            last_code = code

            try:
                fig = self._execute_code(code, df)

                # Validation : vérifier que le graphique a des données
                fig_json = json.loads(fig.to_json())
                has_data = False
                for trace in fig_json.get('data', []):
                    if trace.get('x') or trace.get('y') or trace.get('values') or trace.get('z'):
                        has_data = True
                        break

                if not has_data:
                    raise ValueError("Le graphique généré ne contient aucune donnée visible")

                return {
                    "plotly_json": fig_json,
                    "code": code
                }

            except Exception as e:
                last_error = e
                continue

        # Toutes les tentatives ont échoué -> fallback intelligent
        fig = self._build_fallback(proposal, df)
        return {
            "plotly_json": json.loads(fig.to_json()),
            "code": f"# Code auto-généré (fallback après erreur : {str(last_error)})\n{last_code}"
        }
