import torch.nn as nn

# Simple Multilayered perceptron class with 7 layers in total input Layer , 5 hidden layers and output layer

class ScamClassifier(nn.Module):
    def __init__(self,input_dim):
        super(ScamClassifier, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 128), # input Layer
            # nn.GELU(approximate='tanh'), we were using gelu earlier but relu is giving better results
            nn.ReLU(), # Layer1 activation function
            nn.Dropout(0.4), # Layer1 dropout rate
            nn.Linear(128,256), # 1st hidden layer
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256,256), # 2nd hidden layer
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256,128), # 3rd hidden layer
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128,64), # 4th hidden layer
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64,32), # 5th hidden layer
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32,1), # output layer
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.fc(x)

