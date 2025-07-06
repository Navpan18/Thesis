from pathlib import Path
import pandas as pd

dataset_root = Path("/home/navpan/approaches/PlantVillage_dataset_balanced")
splits = ["train", "val", "test"]
rows = []

for split in splits:
    split_path = dataset_root / split
    if not split_path.exists():
        continue

    for img_path in split_path.rglob("*"):
        if not img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            continue

        try:
            class_folder = img_path.parent.name
            if "___" in class_folder:
                plant, _ = class_folder.split("___", 1)
            else:
                plant, _ = class_folder.split("_", 1)

            rel_path = img_path.relative_to(dataset_root)
            rows.append((str(rel_path), plant.lower()))
        except Exception as e:
            print(f"Skipping {img_path}: {e}")

# Save updated image_species.csv
metadata_dir = dataset_root / "metadata"
metadata_dir.mkdir(exist_ok=True)
species_df = pd.DataFrame(rows, columns=["rel_path", "species"])
species_df.to_csv(metadata_dir / "image_species.csv", index=False)

print(f"✅ Total images indexed: {len(species_df)}")
print(f"✅ Unique species found: {species_df['species'].nunique()}")
