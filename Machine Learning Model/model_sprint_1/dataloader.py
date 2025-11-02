from torch.utils.data import DataLoader, ConcatDataset
from dataset import ScamDataset

# Processing the data in the model format
def create_dataloaders(X_train_vec, X_test_vec, y_train, y_test, BATCH_SIZE):
    train_dataset = ScamDataset(X_train_vec, y_train)
    test_dataset = ScamDataset(X_test_vec, y_test)
    combined_dataset = ConcatDataset([train_dataset, test_dataset])
    combined_loader = DataLoader(combined_dataset, batch_size=BATCH_SIZE, shuffle=True)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)
    return train_loader, test_loader, combined_loader
