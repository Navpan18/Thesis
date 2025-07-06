import pandas as pd
from pathlib import Path
from PIL import Image
from torchvision import transforms
from torch.utils.data import Dataset


class SupConDataset(Dataset):
    def __init__(self, root, label_map_csv, transform=None):
        self.root = Path(root)
        self.transform = transform or transforms.ToTensor()
        label_map = (
            pd.read_csv(label_map_csv, header=None, names=["orig", "canon"])
            .set_index("orig")["canon"]
            .to_dict()
        )

        self.samples = []
        self.targets = []
        self.class_to_idx = {}
        class_id = 0

        for folder in sorted((self.root).iterdir()):
            if not folder.is_dir():
                continue
            label = label_map[folder.name]
            if label not in self.class_to_idx:
                self.class_to_idx[label] = class_id
                class_id += 1
            label_id = self.class_to_idx[label]
            for img_path in folder.glob("*.jpg"):
                self.samples.append(img_path)
                self.targets.append(label_id)

    def __getitem__(self, idx):
        img = Image.open(self.samples[idx]).convert("RGB")
        img = self.transform(img)
        target = self.targets[idx]
        return img, target

    def __len__(self):
        return len(self.samples)
