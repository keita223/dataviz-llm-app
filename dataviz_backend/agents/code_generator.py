import anthropic
import pandas as pd
from io import StringIO, BytesIO
import matplotlib
matplotlib.use('Agg')  # Backend sans GUI pour le serveur
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import base64
import gc


class CodeGeneratorAgent:
    """Agent 3 : Génère le code matplotlib via LLM et retourne l'image"""

    MAX_ROWS_VIZ = 10000  # Echantillonner si plus de 10000 lignes

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-3-haiku-20240307"

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie le DataFrame"""
        unnamed_cols = [c for c in df.columns if 'Unnamed' in str(c)]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)
        return df

    def _build_prompt(self, proposal: dict, df: pd.DataFrame, error_msg: str = None) -> str:
        """Construit le prompt pour générer du code matplotlib"""
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        variables = proposal.get('variables', [])
        valid_vars = [v for v in variables if v in df.columns]
        invalid_vars = [v for v in variables if v not in df.columns]

        vars_warning = ""
        if invalid_vars:
            vars_warning = f"\nATTENTION : Ces colonnes N'EXISTENT PAS : {invalid_vars}. Utilise seulement les colonnes listées ci-dessous."

        retry_info = ""
        if error_msg:
            retry_info = f"\nTA TENTATIVE PRÉCÉDENTE A ÉCHOUÉ AVEC : {error_msg}\nCorrige le code pour éviter cette erreur.\n"

        prompt = f"""Tu es un expert Python en data visualization avec matplotlib et seaborn.
Génère du code Python pour créer cette visualisation.

VISUALISATION :
- Titre : {proposal['title']}
- Type : {proposal['chart_type']}
- Variables : {valid_vars if valid_vars else variables}
{vars_warning}

DONNÉES :
- Colonnes : {list(df.columns)}
- Colonnes numériques : {numeric_cols}
- Colonnes catégorielles : {categorical_cols}
- Nombre de lignes : {len(df)}
- Aperçu :
{df.head(8).to_string()}
{retry_info}
RÈGLES OBLIGATOIRES :
1. Le DataFrame s'appelle 'df'. Il est déjà chargé.
2. matplotlib.pyplot est importé comme 'plt', seaborn comme 'sns', numpy comme 'np'.
3. Commence par plt.figure(figsize=(12, 7))
4. AGRÈGE les données si nécessaire (groupby, value_counts) AVANT de tracer.
5. Pour un pie chart : limite à 8 catégories max (regroupe le reste dans "Autre").
6. Pour un bar chart : trie par valeur décroissante, limite à 15 barres max.
7. Pour un scatter avec beaucoup de points : utilise alpha=0.5.
8. Titre lisible avec plt.title(..., fontsize=16, fontweight='bold')
9. Labels d'axes avec plt.xlabel/plt.ylabel(..., fontsize=13)
10. plt.tight_layout() à la fin.
11. Si les labels x sont longs, utilise plt.xticks(rotation=45, ha='right')
12. Utilise sns.set_style('whitegrid') au début.
13. NE PAS appeler plt.show() ni plt.savefig().
14. NE PAS créer de nouveau DataFrame à partir de zéro, utilise 'df'.
15. Vérifie que les colonnes utilisées EXISTENT dans {list(df.columns)}.

Réponds UNIQUEMENT avec du code Python exécutable.
PAS de ```python, PAS de texte explicatif, PAS de markdown. Juste le code."""

        return prompt

    def _clean_code(self, code: str) -> str:
        """Nettoie le code généré"""
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        lines = code.split('\n')
        clean_lines = []
        for l in lines:
            stripped = l.strip()
            # Supprimer les lignes non-code
            if stripped.startswith(('Voici', 'Here', 'Ce code', 'This code', 'Le code')):
                continue
            # Supprimer plt.show() et plt.savefig()
            if 'plt.show()' in stripped or 'plt.savefig(' in stripped:
                continue
            clean_lines.append(l)

        return '\n'.join(clean_lines).strip()

    def _execute_and_capture(self, code: str, df: pd.DataFrame) -> str:
        """Exécute le code matplotlib et capture l'image en base64"""
        plt.close('all')

        local_scope = {
            "df": df,
            "plt": plt,
            "sns": sns,
            "np": np,
            "pd": pd
        }

        exec(code, local_scope)

        # Capturer la figure courante
        fig = plt.gcf()

        # Vérifier que la figure a du contenu
        if not fig.get_axes():
            raise ValueError("Le code n'a créé aucun graphique")

        # Sauvegarder en PNG base64 (DPI 100 pour economiser la memoire)
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close('all')

        if len(img_base64) < 1000:
            raise ValueError("L'image générée est trop petite, probablement vide")

        return img_base64

    async def generate_visualization(self, proposal: dict, csv_data: str) -> dict:
        """Génère la visualisation matplotlib via LLM avec retry"""
        df = pd.read_csv(StringIO(csv_data))
        df = self._clean_dataframe(df)

        # Echantillonner si le dataset est trop gros (economie memoire)
        if len(df) > self.MAX_ROWS_VIZ:
            df = df.sample(self.MAX_ROWS_VIZ, random_state=42)

        max_retries = 3
        last_error = None
        last_code = ""

        for attempt in range(max_retries):
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
                img_base64 = self._execute_and_capture(code, df)
                del df
                gc.collect()

                return {
                    "image_base64": img_base64,
                    "code": code
                }

            except Exception as e:
                last_error = e
                plt.close('all')
                continue

        # Toutes les tentatives ont échoué -> fallback déterministe
        plt.close('all')
        img_base64 = self._build_fallback(proposal, df)
        del df
        gc.collect()

        return {
            "image_base64": img_base64,
            "code": f"# Fallback (erreur LLM : {str(last_error)})\n{last_code}"
        }

    def _build_fallback(self, proposal: dict, df: pd.DataFrame) -> str:
        """Construit un graphique fallback déterministe et retourne le base64"""
        chart_type = proposal.get('chart_type', 'bar').lower()
        title = proposal.get('title', 'Visualisation')

        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        x_col = categorical_cols[0] if categorical_cols else None
        y_col = numeric_cols[0] if numeric_cols else None

        sns.set_style('whitegrid')
        plt.figure(figsize=(12, 7))

        if chart_type == 'pie' and x_col and y_col:
            agg = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
            if len(agg) > 8:
                top = agg.head(7)
                top['Autre'] = agg.iloc[7:].sum()
                agg = top
            plt.pie(agg.values, labels=agg.index, autopct='%1.1f%%', startangle=90)

        elif chart_type == 'scatter' and len(numeric_cols) >= 2:
            plot_df = df if len(df) <= 1000 else df.sample(1000, random_state=42)
            plt.scatter(plot_df[numeric_cols[0]], plot_df[numeric_cols[1]], alpha=0.5)
            plt.xlabel(numeric_cols[0].replace('_', ' ').title(), fontsize=13)
            plt.ylabel(numeric_cols[1].replace('_', ' ').title(), fontsize=13)

        elif chart_type == 'box' and x_col and y_col:
            top_cats = df[x_col].value_counts().head(10).index
            plot_df = df[df[x_col].isin(top_cats)]
            sns.boxplot(data=plot_df, x=x_col, y=y_col)
            plt.xticks(rotation=45, ha='right')

        elif chart_type == 'histogram' and y_col:
            plt.hist(df[y_col].dropna(), bins=30, edgecolor='white')
            plt.xlabel(y_col.replace('_', ' ').title(), fontsize=13)

        elif x_col and y_col:
            agg = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(15)
            plt.barh(agg.index, agg.values)
            plt.xlabel(y_col.replace('_', ' ').title(), fontsize=13)

        else:
            if numeric_cols:
                plt.hist(df[numeric_cols[0]].dropna(), bins=30, edgecolor='white')
            else:
                counts = df[df.columns[0]].value_counts().head(10)
                plt.barh(counts.index, counts.values)

        plt.title(title, fontsize=16, fontweight='bold')
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close('all')

        return img_base64
