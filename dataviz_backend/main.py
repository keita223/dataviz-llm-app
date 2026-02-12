from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .orchestrator import MultiAgentOrchestrator
from .models import GenerateVizRequest
import io
import traceback
import os

app = FastAPI(title="DataViz LLM API", version="1.0.0")

# CORS (important pour React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, spécifie ton domaine frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = MultiAgentOrchestrator()

# Servir les fichiers statiques (frontend)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.post("/api/analyze")
async def analyze_and_propose(
    problem: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Endpoint 1 : Upload CSV + problématique → Retourne 3 propositions
    """
    try:
        # Lire le CSV
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        
        # Orchestrer Agents 1 + 2
        result = await orchestrator.get_proposals(problem, csv_data)
        
        return result
    
    except Exception as e:
        print("=== ERREUR /api/analyze ===")
        traceback.print_exc()
        print("===========================")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_visualization(request: GenerateVizRequest):
    """
    Endpoint 2 : Proposition choisie + CSV → Génère la visualisation
    """
    try:
        result = await orchestrator.generate_viz(
            proposal=request.proposal.dict(),
            csv_data=request.csv_data
        )
        return result

    except Exception as e:
        print("=== ERREUR /api/generate ===")
        traceback.print_exc()
        print("============================")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}