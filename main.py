import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, datasets

train = datasets.MNIST("", train=True, download=True,
                      transform = transforms.Compose([transforms.ToTensor()]))
test = datasets.MNIST("", train=False, download=True,
                      transform = transforms.Compose([transforms.ToTensor()]))
 
trainset = torch.utils.data.DataLoader(train, batch_size=15, shuffle=True)
testset = torch.utils.data.DataLoader(test, batch_size=15, shuffle=True)

class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 86)
        self.fc2 = nn.Linear(86, 86)
        self.fc3 = nn.Linear(86, 86)
        self.fc4 = nn.Linear(86, 10)
 
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return F.log_softmax(x, dim=1)
 
model = NeuralNetwork()

optimizer = optim.Adam(model.parameters(), lr=0.001)
EPOCHS = 2
for epoch in range(EPOCHS):
    for data in trainset:
        X, y = data
        model.zero_grad()
        output = model(X.view(-1, 28 * 28))
        loss = F.nll_loss(output, y)
        loss.backward()
        optimizer.step()
    # print(loss)

correct = 0
total = 0
with torch.no_grad():
    for data in testset:
        data_input, target = data
        output = model(data_input.view(-1, 784))
        for idx, i in enumerate(output):
            if torch.argmax(i) == target[idx]:
                correct += 1
            total += 1
 
print('Accuracy: %d %%' % (100 * correct / total))
print(torch.argmax(model(X[1].view(-1, 784))[0]))

plt.imshow(X[1].view(28,28))
plt.show()