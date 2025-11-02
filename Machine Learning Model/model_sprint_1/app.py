import os
import torch
import torch.nn as nn
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from model import ScamClassifier  

MODEL_PATH = "C:/Apps/SPRINT_1_MODEL/model/scam_model_RNN.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class Message(BaseModel):
    text: str

def load_model():
    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
    vectorizer = checkpoint["vectorizer"]
    input_dim = getattr(vectorizer, "max_features", None)
    if input_dim is None:
        raise ValueError("vectorizer has no attribute max_features")
    model = ScamClassifier(input_dim)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(DEVICE)
    model.eval()
    return model, vectorizer

model, vectorizer = load_model()
app = FastAPI(title="Scam Detection API", version="1.0")

@app.get("/")
def home():
    return {"message": "Scam Detection API is running"}

@app.post("/predict")
def predict(msg: Message):
    features = vectorizer.transform([msg.text]).toarray()
    features_tensor = torch.tensor(features, dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        output = model(features_tensor).item()
    label = "scam" if output >= 0.5 else "normal"
    return {"text": msg.text, "prediction": label, "probability": round(output, 4)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
