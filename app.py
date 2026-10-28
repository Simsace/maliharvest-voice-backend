import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import maliba_ai

app = FastAPI(title="MaliHarvest Voice API")

# Autorise votre site Vercel à communiquer avec Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation automatique en testant les structures possibles de la bibliothèque
tts = None
try:
    if hasattr(maliba_ai, "BambaraTTS"):
        tts = maliba_ai.BambaraTTS()
    elif hasattr(maliba_ai, "TTS"):
        tts = maliba_ai.TTS()
    else:
        # Si la classe est cachée dans un sous-module, on cherche le synthétiseur alternatif
        from maliba_ai.tts import BambaraTTS
        tts = BambaraTTS()
except Exception as e:
    print(f"Tentative d'initialisation alternative... Erreur initiale : {e}")
    try:
        from maliba_ai.models import TTS
        tts = TTS()
    except Exception as e2:
        print(f"Échec total du chargement de la classe : {e2}")
        tts = None

class TTSRequest(BaseModel):
    text: str

@app.post("/generate")
async def generate_voice(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte est vide")
    
    if tts is None:
        raise HTTPException(status_code=500, detail="Le moteur vocal MALIBA-AI n'a pas pu être chargé")

    # Suppression des anciens fichiers pour ne pas saturer Render
    for f in glob.glob("*.wav"):
        try:
            os.remove(f)
        except:
            pass

    output_filename = "output_maliharvest.wav"
    
    try:
        # Synthèse du texte en voix humaine bambara
        if hasattr(tts, "synthesize"):
            tts.synthesize(request.text, output_filename)
        elif hasattr(tts, "generate"):
            tts.generate(request.text, output_filename)
        else:
            raise AttributeError("La méthode de génération du modèle est introuvable")
        
        if os.path.exists(output_filename):
            return FileResponse(output_filename, media_type="audio/wav")
        else:
            raise HTTPException(status_code=500, detail="Le fichier audio n'a pas été créé")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "online", "message": "API MaliHarvest connectée à MALIBA-AI"}
