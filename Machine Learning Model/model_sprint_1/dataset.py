import torch

# Dataset class for scam detection, in this class we will load the data and preprocess it
class ScamDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels):
        self.texts = texts    
        self.labels = labels

    def __len__(self):
        return self.labels.shape[0]  

    def __getitem__(self, idx):
        row = self.texts[idx].toarray().squeeze().astype('float32')  
        return torch.tensor(row, dtype=torch.float32), torch.tensor(self.labels[idx], dtype=torch.float32)
