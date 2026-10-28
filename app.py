import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importations exactes selon la documentation officielle de MALIBA-AI
from maliba_ai.tts.inference import BambaraTTSInference

app = FastAPI(title="MaliHarvest Voice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation paresseuse pour économiser la mémoire de Render
tts_model = None

def get_tts_instance():
    global tts_model
    if tts_model is None:
        try:
            # Instance officielle de génération vocale
            tts_model = BambaraTTSInference()
            print("Moteur vocal MALIBA-AI initialisé avec succès.")
        except Exception as e:
            print(f"Échec de l'initialisation du modèle officiel : {e}")
            tts_model = None
    return tts_model

class TTSRequest(BaseModel):
    text: str

@app.post("/generate")
async def generate_voice(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte envoyé est vide")
    
    model = get_tts_instance()
    if model is None:
        raise HTTPException(
            status_code=500, 
            detail="Le moteur vocal MALIBA-AI n'a pas pu être chargé (RAM insuffisante sur Render)"
        )

    # Nettoyage des anciens fichiers audio
    for f in glob.glob("*.wav"):
        try:
            os.remove(f)
        except:
            pass

    output_filename = "output_maliharvest.wav"
    
    try:
        # Génération de la parole selon la fonction officielle du SDK
        import soundfile as sf
        audio_data = model.generate_speech(request.text)
        
        # Enregistrement du fichier audio au format WAV standard (16kHz)
        sf.write(output_filename, audio_data, 16000)
        
        if os.path.exists(output_filename):
            return FileResponse(output_filename, media_type="audio/wav")
        else:
            raise HTTPException(status_code=500, detail="Le fichier audio n'a pas pu être écrit")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur pendant la génération : {str(e)}")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API MaliHarvest configurée avec l'importation officielle MALIBA-AI"}
