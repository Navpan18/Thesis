from pathlib import Path
from collections import Counter
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset


class DANNDataset(Dataset):
    def __init__(
        self,
        root,
        label_map_csv,
        image_species_csv,
        transform=None,
        exclude_species=None,
        include_only_species=None,
        disease_filter=None,
    ):
        self.root = Path(root)
        self.transform = transform
        label_df = pd.read_csv(label_map_csv, header=None, names=["folder", "disease"])
        label_map = dict(zip(label_df.folder, label_df.disease))
        species_df = pd.read_csv(image_species_csv)

        raw = []
        for _, row in species_df.iterrows():
            rel_path = row["rel_path"]
            species = row["species"]
            folder = Path(rel_path).parts[1]
            disease = label_map.get(folder)
            if disease_filter and disease != disease:
                continue
            if exclude_species and species == exclude_species:
                continue
            if include_only_species and species != include_only_species:
                continue
            raw.append((rel_path, disease, species))

        if not raw:
            raise ValueError("❌ No samples after filtering.")

        self.class_to_idx = {}
        self.species_to_idx = {}
        self.samples = []

        for rel, dis, sp in raw:
            self.class_to_idx.setdefault(dis, len(self.class_to_idx))
            self.species_to_idx.setdefault(sp, len(self.species_to_idx))
            d_id = self.class_to_idx[dis]
            s_id = self.species_to_idx[sp]
            self.samples.append((rel, d_id, s_id))

        print(f"\n🔍 Loaded DANNDataset | Samples: {len(self.samples)}")
        print(f"🧬 Disease classes: {self.class_to_idx}")
        print(f"🌿 Species classes: {self.species_to_idx}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rel, d_id, s_id = self.samples[idx]
        img = Image.open(self.root / rel).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, d_id, s_id
