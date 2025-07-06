
import os
import torch
import matplotlib.pyplot as plt
import numpy as np
from torchvision import transforms
from torch.utils.data import DataLoader
from PIL import Image
import cv2
import pandas as pd
from dataset import DANNDataset
from dann_model import DANNModel

# === Config ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
test_root = "/home/navpan/approaches/PlantVillage_dataset_balanced/"
label_map = f"../../PlantVillage_dataset_balanced/metadata/label_map.csv"
image_species = f"../../PlantVillage_dataset_balanced/metadata/image_species.csv"
model_weights = "model_full_dann.pth"
gradcam_dir = "gradcam"
os.makedirs(gradcam_dir, exist_ok=True)

# === Transforms ===
transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ]
)

# === Dataset
print("🔄 Loading test dataset...")
ds = DANNDataset(test_root, label_map, image_species, transform=transform)
class_to_idx = ds.class_to_idx
idx_to_class = {v: k for k, v in class_to_idx.items()}

# === Model
print("🧠 Loading trained model...")
model = DANNModel(len(class_to_idx), len(ds.species_to_idx))
model.load_state_dict(torch.load(model_weights, map_location=device), strict=False)
model.to(device)
model.eval()

# === Hooks
gradients = []
features = []


def backward_hook(module, grad_input, grad_output):
    gradients.append(grad_output[0])


def forward_hook(module, input, output):
    features.append(output)


# Register both hooks
target_layer = model.encoder.layer4[2].conv3
target_layer.register_forward_hook(forward_hook)
target_layer.register_backward_hook(backward_hook)

# === Sample 2 test images per disease
print("🧪 Sampling 2 images per class...")
samples_per_class = {k: [] for k in class_to_idx.keys()}
for img, label, _ in ds:
    name = idx_to_class[label]
    if len(samples_per_class[name]) < 2:
        samples_per_class[name].append((img, label))
    if all(len(v) >= 2 for v in samples_per_class.values()):
        break

# === Generate Grad-CAMs
print("🎯 Starting Grad-CAM generation...")
for disease, img_list in samples_per_class.items():
    print(f"🎨 Processing: {disease}")
    fig, axs = plt.subplots(2, 2, figsize=(8, 8))

    for i, (img_tensor, label) in enumerate(img_list):
        gradients.clear()
        features.clear()

        img_input = img_tensor.unsqueeze(0).to(device)
        img_input.requires_grad = True

        # Forward + Backward
        out, _ = model(img_input)
        model.zero_grad()
        out[0, label].backward()

        fmap = features[-1][0].detach().cpu()  # [C,H,W]
        grad = gradients[-1][0].detach().cpu()  # [C,H,W]

        weights = torch.mean(grad, dim=(1, 2), keepdim=True)
        cam = torch.sum(weights * fmap, dim=0).numpy()
        cam = np.maximum(cam, 0)
        cam = cv2.resize(cam, (224, 224))
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

        # Overlay
        img_np = img_tensor.permute(1, 2, 0).cpu().numpy()
        img_np = (img_np - img_np.min()) / (img_np.max() - img_np.min() + 1e-8)
        heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
        heatmap = np.float32(heatmap) / 255
        overlay = np.clip(heatmap * 0.5 + img_np, 0, 1)

        axs[0, i].imshow(img_np)
        axs[0, i].set_title("Original")
        axs[1, i].imshow(overlay)
        axs[1, i].set_title("Grad-CAM")
        for ax in axs[:, i]:
            ax.axis("off")

    plt.tight_layout()
    out_path = os.path.join(gradcam_dir, f"{disease.replace(' ', '_')}.png")
    plt.savefig(out_path)
    plt.close()
    print(f"✅ Saved: {out_path}")

print("\n✅ All Grad-CAMs done and saved to gradcam/")
