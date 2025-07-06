import torch
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import umap
import numpy as np
from torch.utils.data import DataLoader, Subset
from dataset import DANNDataset
from dann_model import DANNModel
from torchvision import transforms
import random

# === Config ===
root = "/home/navpan/approaches/PlantVillage_dataset_balanced"
model_weights = "model_full_dann.pth"  # your trained model
label_map = f"{root}/metadata/label_map.csv"
image_species = f"{root}/metadata/image_species.csv"
batch_size = 64
n_samples = 1000  # limit for faster UMAP

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# === Transform ===
transform = transforms.Compose(
    [transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor()]
)

# === Dataset & loader
ds = DANNDataset(root, label_map, image_species, transform=transform)
indices = random.sample(range(len(ds)), k=min(n_samples, len(ds)))
loader = DataLoader(Subset(ds, indices), batch_size=batch_size, shuffle=False)

# === Load model
model = DANNModel(num_disease=len(ds.class_to_idx), num_species=len(ds.species_to_idx))
model.load_state_dict(torch.load(model_weights, map_location=device), strict=False)
model.to(device)
model.eval()

# === Extract features
features = []
diseases = []
species = []

with torch.no_grad():
    for x, y_d, y_s in loader:
        x = x.to(device)
        f = model.encoder(x).cpu().numpy()
        features.append(f)
        diseases += y_d.tolist()
        species += y_s.tolist()

features = np.vstack(features)

# === UMAP
reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
emb = reducer.fit_transform(features)

# === Plot by disease
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.scatter(emb[:, 0], emb[:, 1], c=diseases, cmap="tab20", s=10)
plt.title("UMAP: Colored by Disease")
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")

# === Plot by species
plt.subplot(1, 2, 2)
plt.scatter(emb[:, 0], emb[:, 1], c=species, cmap="tab20b", s=10)
plt.title("UMAP: Colored by Species")
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")

plt.tight_layout()
plt.savefig("umap_disease_species.png")
plt.show()
print("✅ UMAP saved as 'umap_disease_species.png'")
