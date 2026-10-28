import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import maliba_ai

app = FastAPI(title="MaliHarvest Voice API")

# Autorise votre site web (VS Code / Vercel) à communiquer avec Render sans blocage CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable globale pour stocker le modèle une fois chargé
tts_model = None

def get_tts_instance():
    """
    Charge le modèle en mémoire uniquement à la demande pour économiser la RAM sur Render.
    Teste les différentes structures possibles de la bibliothèque MALIBA-AI.
    """
    global tts_model
    if tts_model is None:
        try:
            if hasattr(maliba_ai, "BambaraTTS"):
                tts_model = maliba_ai.BambaraTTS()
            elif hasattr(maliba_ai, "TTS"):
                tts_model = maliba_ai.TTS()
            else:
                from maliba_ai.tts import BambaraTTS
                tts_model = BambaraTTS()
            print("Moteur vocal MALIBA-AI chargé avec succès.")
        except Exception as e:
            print(f"Tentative 1 d'initialisation échouée : {e}")
            try:
                from maliba_ai.models import TTS
                tts_model = TTS()
                print("Moteur vocal MALIBA-AI chargé via le sous-module 'models'.")
            except Exception as e2:
                print(f"Échec total du chargement de la classe MALIBA-AI : {e2}")
                tts_model = None
    return tts_model

class TTSRequest(BaseModel):
    text: str

@app.post("/generate")
async def generate_voice(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte envoyé est vide")
    
    # Récupération ou chargement du modèle
    model = get_tts_instance()
    if model is None:
        raise HTTPException(
            status_code=500, 
            detail="Le moteur vocal MALIBA-AI n'a pas pu être chargé (Mémoire RAM insuffisante sur Render)"
        )

    # Nettoyage des anciens fichiers audio pour ne pas saturer le disque dur gratuit
    for f in glob.glob("*.wav"):
        try:
            os.remove(f)
        except:
            pass

    output_filename = "output_maliharvest.wav"
    
    try:
        # Synthèse du texte en voix humaine selon la méthode disponible dans le SDK
        if hasattr(model, "synthesize"):
            model.synthesize(request.text, output_filename)
        elif hasattr(model, "generate"):
            model.generate(request.text, output_filename)
        else:
            raise AttributeError("La méthode de génération vocale (synthesize/generate) est introuvable")
        
        # Vérification et envoi du fichier audio
        if os.path.exists(output_filename):
            return FileResponse(output_filename, media_type="audio/wav")
        else:
            raise HTTPException(status_code=500, detail="Le fichier audio n'a pas été créé sur le disque")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur pendant la génération : {str(e)}")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API MaliHarvest connectée à MALIBA-AI"}
