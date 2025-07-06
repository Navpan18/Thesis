import matplotlib.pyplot as plt
from PIL import Image
from blur_utils import blur_background_pil  # Make sure this is in the same folder or import path

# === Pick an image path from your dataset
img_path = "/home/navpan/approaches/PlantVillage_dataset_balanced/train/Tomato___Bacterial_spot/image (1).JPG"

# === Load and process
original = Image.open(img_path).convert("RGB")
blurred = blur_background_pil(original)

# === Show side by side
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(original)
plt.title("Original")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(blurred)
plt.title("Blurred Background")
plt.axis("off")

plt.tight_layout()
plt.savefig("./blurred_comparison.png")
print("Figure saved as blurred_comparison.png")
# plt.show()
