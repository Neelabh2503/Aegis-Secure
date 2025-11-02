# Importing necessary libraries
import os
import torch
import dotenv

dotenv.load_dotenv()  # Loading the .env variables that are required for model training

from preprocess import load_and_preprocess
from dataloader import create_dataloaders
from model import ScamClassifier
from train_eval import train_model, evaluate_and_save

DATA_PATH = os.getenv("DATA_PATH")
BATCH_SIZE = int(os.getenv("BATCH_SIZE"))
EPOCHS = int(os.getenv("EPOCHS"))
LEARNING_RATE = float(os.getenv("LEARNING_RATE"))
MODEL_DIR = os.getenv("MODEL_DIR")
MAX_FEATURES = int(os.getenv("MAX_FEATURES"))

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if DEVICE.type == 'cuda':
    print("Gpu is available name :", torch.cuda.get_device_name(0))
else:
    print("Using cpu device")

X_train_vec, X_test_vec, y_train, y_test, vectorizer = load_and_preprocess(DATA_PATH, MAX_FEATURES)
train_loader, test_loader, combined_loader = create_dataloaders(X_train_vec, X_test_vec, y_train, y_test, BATCH_SIZE)

model = ScamClassifier(X_train_vec.shape[1]).to(DEVICE)
model = train_model(model, train_loader, DEVICE, EPOCHS, LEARNING_RATE)
evaluate_and_save(model, combined_loader, DEVICE, vectorizer, MODEL_DIR)
