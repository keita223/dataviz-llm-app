from .agents.data_analyst import DataAnalystAgent
from .agents.viz_strategist import VizStrategistAgent
from .agents.code_generator import CodeGeneratorAgent
from .models import DataSummary, VizProposal

class MultiAgentOrchestrator:
    """Orchestre les 3 agents"""
    
    def __init__(self):
        self.data_analyst = DataAnalystAgent()
        self.viz_strategist = VizStrategistAgent()
        self.code_generator = CodeGeneratorAgent()
    
    async def get_proposals(self, problem: str, csv_data: str) -> dict:
        """
        Étape 1 + 2 : Analyse + Propositions
        """
        # Agent 1 : Analyse
        data_summary = await self.data_analyst.analyze(csv_data, problem)
        
        # Agent 2 : Propositions
        proposals = await self.viz_strategist.propose_visualizations(data_summary, problem)
        
        return {
            "data_summary": data_summary,
            "proposals": proposals
        }
    
    async def generate_viz(self, proposal: dict, csv_data: str) -> dict:
        """
        Étape 3 : Génération de la visualisation
        """
        return await self.code_generator.generate_visualization(proposal, csv_data)