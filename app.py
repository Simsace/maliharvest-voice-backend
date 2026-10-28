import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from maliba_ai import BambaraTTS

app = FastAPI(title="MaliHarvest Voice API")

# Permet à votre site sur Vercel de contacter Render sans blocage de sécurité
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chargement du modèle de voix malienne
try:
    tts = BambaraTTS()
except Exception as e:
    print(f"Erreur d'initialisation du modèle : {e}")
    tts = None

class TTSRequest(BaseModel):
    text: str

@app.post("/generate")
async def generate_voice(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte est vide")
    
    if tts is None:
        raise HTTPException(status_code=500, detail="Le moteur vocal n'est pas prêt")

    # Nettoyage automatique des anciens fichiers .wav pour économiser l'espace de Render
    for f in glob.glob("*.wav"):
        try:
            os.remove(f)
        except:
            pass

    output_filename = "output_maliharvest.wav"
    
    try:
        # L'IA génère la voix humaine en bambara
        tts.synthesize(request.text, output_filename)
        
        if os.path.exists(output_filename):
            return FileResponse(output_filename, media_type="audio/wav")
        else:
            raise HTTPException(status_code=500, detail="Échec de la génération audio")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "online", "message": "API MaliHarvest active"}
