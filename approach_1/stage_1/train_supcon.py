import torch, torch.nn as nn, torch.optim as optim
from torchvision import models, transforms
from torch.utils.data import DataLoader
from supcon_dataset import SupConDataset
from supcon_loss import SupConLoss
import torch.nn.functional as F

# === Config ===
data_path = "/home/navpan/approaches/PlantVillage_dataset_balanced/train"
label_map = (
    "/home/navpan/approaches/PlantVillage_dataset_balanced/metadata/label_map.csv"
)
batch_size = 128
epochs = 20
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# === Data loader ===
transform = transforms.Compose(
    [
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
    ]
)

train_dataset = SupConDataset(data_path, label_map, transform=transform)
train_loader = DataLoader(
    train_dataset, batch_size=batch_size, shuffle=True, num_workers=4
)

# === Model & Loss ===
resnet = models.resnet50(weights=None)
resnet.fc = nn.Sequential(nn.Linear(2048, 256), nn.ReLU(), nn.Linear(256, 128))
resnet.to(device)

criterion = SupConLoss()
optimizer = optim.Adam(resnet.parameters(), lr=1e-3)

# === Training loop ===
for epoch in range(epochs):
    resnet.train()
    total_loss = 0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        features = F.normalize(resnet(images), dim=1)
        loss = criterion(features, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    print(f"[{epoch+1}/{epochs}] Loss: {total_loss/len(train_loader):.4f}")

# === Save encoder weights ===
torch.save(resnet.state_dict(), "supcon_encoder.pth")
