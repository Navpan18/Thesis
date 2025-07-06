import os, numpy as np, torch, torch.nn as nn, torch.optim as optim, random
from torchvision import transforms
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
from datetime import datetime
from dataset import DANNDataset
from dann_model import DANNModel

root = "/home/navpan/approaches/PlantVillage_dataset_balanced"
sup_weights = "../stage_1/supcon_encoder.pth"
log_path = "log_full_dann.txt"
model_out = "model_full_dann.pth"
epochs = 30
batch_size = 64
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def seed_all(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ramp_lambda(epoch, total=30, warm=10, cap=0.3):
    if epoch < warm:
        return 0.0
    p = (epoch - warm) / (total - warm)
    return min(cap, (2 / (1 + np.exp(-10 * p)) - 1) * cap)


seed_all()

# === Transforms ===
tf_train = transforms.Compose(
    [
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
    ]
)
tf_val = transforms.Compose(
    [transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor()]
)

# === Dataset ===
ds = DANNDataset(
    root,
    f"{root}/metadata/label_map.csv",
    f"{root}/metadata/image_species.csv",
    transform=tf_train,
)
val_len = int(0.1 * len(ds))
train_len = len(ds) - val_len
train_ds, val_ds = random_split(ds, [train_len, val_len])
val_ds.dataset.transform = tf_val

tl = DataLoader(train_ds, batch_size, shuffle=True, num_workers=4)
vl = DataLoader(val_ds, batch_size, shuffle=False, num_workers=4)

n_dis = len(ds.class_to_idx)
n_sp = len(ds.species_to_idx)

print(f"\n🔁 Full Dataset DANN Training")
print(f"📊 Train: {len(train_ds)} | Val: {len(val_ds)}")
print(f"🧬 Disease classes: {n_dis} | 🌿 Species classes: {n_sp}\n")

# === Model ===
model = DANNModel(n_dis, n_sp, lambda_init=0.0, plant_head_type="linear")
model.encoder.load_state_dict(torch.load(sup_weights), strict=False)
model.to(device)

ce = nn.CrossEntropyLoss()
opt = optim.Adam(model.parameters(), lr=1e-4)

# === Logging ===
with open(log_path, "w") as f:
    f.write(f"# Full-DANN log {datetime.now()}\n")
    f.write("ep\tλ\ttrCE\ttrDom\tspAcc\tvalCE\tvalAcc\n")

# === Training ===
for ep in range(epochs):
    lam = ramp_lambda(ep, total=epochs)
    model.grl.lambda_ = lam
    model.train()
    tr_ce = tr_dom = 0.0
    sp_correct = sp_total = 0

    for x, y_d, y_s in tqdm(tl, desc=f"ep{ep+1:02d} λ={lam:.2f}", leave=False):
        x, y_d, y_s = x.to(device), y_d.to(device), y_s.to(device)
        out_d, out_s = model(x)
        l_ce = ce(out_d, y_d)
        l_dom = ce(out_s, y_s)
        loss = l_ce - lam * l_dom
        opt.zero_grad()
        loss.backward()
        opt.step()
        tr_ce += l_ce.item()
        tr_dom += l_dom.item()
        sp_correct += (out_s.argmax(1) == y_s).sum().item()
        sp_total += y_s.size(0)

    sp_acc = 100 * sp_correct / sp_total

    # === Validation ===
    model.eval()
    val_ce = correct = total = 0
    with torch.no_grad():
        for x, y_d, _ in vl:
            x, y_d = x.to(device), y_d.to(device)
            out_d, _ = model(x)
            val_ce += ce(out_d, y_d).item()
            correct += (out_d.argmax(1) == y_d).sum().item()
            total += y_d.size(0)
    v_ce = val_ce / len(vl)
    v_acc = 100 * correct / total

    print(
        f"✅ ep{ep+1:02d} λ={lam:.2f} trCE={tr_ce/len(tl):.3f} spAcc={sp_acc:.1f}% valAcc={v_acc:.2f}%"
    )
    with open(log_path, "a") as f:
        f.write(
            f"{ep+1}\t{lam:.2f}\t{tr_ce/len(tl):.4f}\t{tr_dom/len(tl):.4f}\t{sp_acc:.2f}\t{v_ce:.4f}\t{v_acc:.2f}\n"
        )

torch.save(model.state_dict(), model_out)
print("✅ Model saved:", model_out)
print("📄 Log saved  :", log_path)
