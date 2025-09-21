import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import os

# Model Training
def train_model(model, train_loader, DEVICE, EPOCHS, LEARNING_RATE):
    criterion = nn.BCELoss() # Binary Cross Entropy Loss
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE) # Using the optimizer as Adam
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0
        for texts, labels in train_loader:
            texts, labels = texts.to(DEVICE), labels.to(DEVICE).unsqueeze(1)
            optimizer.zero_grad()
            outputs = model(texts)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {running_loss/len(train_loader):.4f}")
    return model

# Model Evaluation
def evaluate_and_save(model, combined_loader, DEVICE, vectorizer, MODEL_DIR):
    model.eval()
    y_true = []
    y_pred = []
    with torch.no_grad():
        for texts, labels in combined_loader:
            texts, labels = texts.to(DEVICE), labels.to(DEVICE).unsqueeze(1)
            outputs = model(texts)
            predicted = (outputs >= 0.5).float()
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())

    # Saving the model and predicted and true values for the further analysis , for making the classification report.
    pd.Series(y_true).to_csv("true.csv", index=False)
    pd.Series(y_pred).to_csv("pred.csv", index=False)

    torch.save({
        'model_state_dict': model.state_dict(),
        'vectorizer': vectorizer
    }, os.path.join(MODEL_DIR, "scam_model_RNN.pth"))

    print("Model saved to", os.path.join(MODEL_DIR, "scam_model_RNN.pth"))
