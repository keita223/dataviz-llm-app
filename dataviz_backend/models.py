from pydantic import BaseModel
from typing import List, Optional

class AnalysisRequest(BaseModel):
    """Requête utilisateur avec problématique + données"""
    problem: str
    csv_data: str  # CSV en string

class DataSummary(BaseModel):
    """Résumé de l'analyse des données par Agent 1"""
    column_types: dict
    numeric_stats: dict
    correlations: Optional[dict]
    insights: str

class VizProposal(BaseModel):
    """Une proposition de visualisation"""
    title: str
    chart_type: str  # "scatter", "bar", "box", "heatmap", etc.
    variables: List[str]
    justification: str
    best_practices: str  # Pourquoi c'est conforme aux bonnes pratiques

class ProposalsResponse(BaseModel):
    """Les 3 propositions de l'Agent 2"""
    proposals: List[VizProposal]
    data_summary: DataSummary

class GenerateVizRequest(BaseModel):
    """Requête pour générer la viz finale"""
    proposal: VizProposal
    csv_data: str

class VizResponse(BaseModel):
    """Réponse avec le graphique"""
    plotly_json: dict  # Config Plotly en JSON
    code: str  # Code Python généré (pour transparence)