"""Tests pour les agents et modeles."""
import pytest
import pandas as pd
from io import StringIO
from dataviz_backend.models import VizProposal, GenerateVizRequest, DataSummary
from dataviz_backend.agents.code_generator import CodeGeneratorAgent


# === Tests des modeles Pydantic ===

def test_viz_proposal_valid():
    """Test creation d'une VizProposal valide."""
    proposal = VizProposal(
        title="Test Chart",
        chart_type="bar",
        variables=["col_a", "col_b"],
        justification="Pour comparer",
        best_practices="Lisible"
    )
    assert proposal.title == "Test Chart"
    assert proposal.chart_type == "bar"
    assert len(proposal.variables) == 2


def test_viz_proposal_missing_field():
    """Test qu'une VizProposal sans champ obligatoire echoue."""
    with pytest.raises(Exception):
        VizProposal(
            title="Test",
            chart_type="bar"
            # variables manquant
        )


def test_generate_viz_request_valid():
    """Test creation d'un GenerateVizRequest valide."""
    request = GenerateVizRequest(
        proposal=VizProposal(
            title="Test",
            chart_type="scatter",
            variables=["x", "y"],
            justification="Correlation",
            best_practices="Alpha"
        ),
        csv_data="a,b\n1,2\n3,4"
    )
    assert request.csv_data == "a,b\n1,2\n3,4"
    assert request.proposal.chart_type == "scatter"


def test_data_summary_valid():
    """Test creation d'un DataSummary valide."""
    summary = DataSummary(
        column_types={"col_a": "int64", "col_b": "float64"},
        numeric_stats={"col_a": {"mean": 5.0}},
        correlations=None,
        insights="Donnees bien structurees"
    )
    assert summary.insights == "Donnees bien structurees"
    assert summary.correlations is None


# === Tests du CodeGeneratorAgent (methodes utilitaires) ===

class TestCodeGeneratorUtils:
    """Tests des methodes utilitaires du CodeGeneratorAgent."""

    def setup_method(self):
        self.agent = CodeGeneratorAgent()

    def test_clean_dataframe_removes_unnamed(self):
        """Test que _clean_dataframe supprime les colonnes Unnamed."""
        df = pd.DataFrame({
            "Unnamed: 0": [0, 1, 2],
            "produit": ["A", "B", "C"],
            "prix": [10, 20, 30]
        })
        cleaned = self.agent._clean_dataframe(df)
        assert "Unnamed: 0" not in cleaned.columns
        assert "produit" in cleaned.columns
        assert "prix" in cleaned.columns

    def test_clean_dataframe_keeps_valid_columns(self):
        """Test que _clean_dataframe garde les colonnes normales."""
        df = pd.DataFrame({"a": [1], "b": [2]})
        cleaned = self.agent._clean_dataframe(df)
        assert list(cleaned.columns) == ["a", "b"]

    def test_clean_code_removes_markdown(self):
        """Test que _clean_code supprime le markdown."""
        code = '```python\nplt.bar([1,2],[3,4])\n```'
        cleaned = self.agent._clean_code(code)
        assert "```" not in cleaned
        assert "plt.bar" in cleaned

    def test_clean_code_removes_plt_show(self):
        """Test que _clean_code supprime plt.show()."""
        code = "plt.figure()\nplt.bar([1],[2])\nplt.show()"
        cleaned = self.agent._clean_code(code)
        assert "plt.show()" not in cleaned
        assert "plt.bar" in cleaned

    def test_clean_code_removes_savefig(self):
        """Test que _clean_code supprime plt.savefig()."""
        code = "plt.bar([1],[2])\nplt.savefig('test.png')"
        cleaned = self.agent._clean_code(code)
        assert "savefig" not in cleaned

    def test_clean_code_removes_explanatory_text(self):
        """Test que _clean_code supprime les lignes de texte."""
        code = "Voici le code:\nplt.bar([1],[2])\nCe code fait..."
        cleaned = self.agent._clean_code(code)
        assert "Voici" not in cleaned
        assert "Ce code" not in cleaned
        assert "plt.bar" in cleaned

    def test_build_prompt_contains_chart_info(self):
        """Test que _build_prompt contient les infos du graphique."""
        df = pd.DataFrame({"produit": ["A", "B"], "ventes": [100, 200]})
        proposal = {
            "title": "Ventes par produit",
            "chart_type": "bar",
            "variables": ["produit", "ventes"]
        }
        prompt = self.agent._build_prompt(proposal, df)
        assert "Ventes par produit" in prompt
        assert "bar" in prompt
        assert "produit" in prompt
        assert "ventes" in prompt

    def test_build_prompt_warns_invalid_columns(self):
        """Test que _build_prompt avertit des colonnes invalides."""
        df = pd.DataFrame({"a": [1], "b": [2]})
        proposal = {
            "title": "Test",
            "chart_type": "bar",
            "variables": ["a", "colonne_inexistante"]
        }
        prompt = self.agent._build_prompt(proposal, df)
        assert "N'EXISTENT PAS" in prompt
        assert "colonne_inexistante" in prompt

    def test_build_prompt_includes_retry_info(self):
        """Test que _build_prompt inclut l'erreur precedente en retry."""
        df = pd.DataFrame({"a": [1]})
        proposal = {"title": "Test", "chart_type": "bar", "variables": ["a"]}
        prompt = self.agent._build_prompt(proposal, df, error_msg="KeyError: 'x'")
        assert "KeyError" in prompt
        assert "ÉCHOUÉ" in prompt

    def test_execute_and_capture_returns_base64(self):
        """Test que _execute_and_capture retourne une image base64."""
        import matplotlib
        matplotlib.use('Agg')
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        code = "plt.figure(figsize=(8, 5))\nplt.bar(df['x'], df['y'])\nplt.title('Test')"
        result = self.agent._execute_and_capture(code, df)
        assert isinstance(result, str)
        assert len(result) > 1000  # Image non vide

    def test_execute_and_capture_fails_on_empty(self):
        """Test que _execute_and_capture echoue si pas de graphique."""
        df = pd.DataFrame({"x": [1]})
        code = "x = 1 + 1"  # Pas de graphique
        with pytest.raises(ValueError, match="aucun graphique"):
            self.agent._execute_and_capture(code, df)

    def test_build_fallback_returns_base64(self):
        """Test que _build_fallback retourne une image valide."""
        df = pd.DataFrame({
            "categorie": ["A", "B", "C", "D"],
            "valeur": [10, 20, 30, 40]
        })
        proposal = {"title": "Fallback Test", "chart_type": "bar"}
        result = self.agent._build_fallback(proposal, df)
        assert isinstance(result, str)
        assert len(result) > 1000

    def test_build_fallback_pie(self):
        """Test que le fallback pie fonctionne."""
        df = pd.DataFrame({
            "produit": ["A", "B", "C"],
            "ventes": [100, 200, 300]
        })
        proposal = {"title": "Repartition", "chart_type": "pie"}
        result = self.agent._build_fallback(proposal, df)
        assert isinstance(result, str)
        assert len(result) > 1000

    def test_build_fallback_scatter(self):
        """Test que le fallback scatter fonctionne."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10]
        })
        proposal = {"title": "Correlation", "chart_type": "scatter"}
        result = self.agent._build_fallback(proposal, df)
        assert isinstance(result, str)
        assert len(result) > 1000
