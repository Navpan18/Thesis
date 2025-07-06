import matplotlib.pyplot as plt
import pandas as pd
import io  # ✅ FIX: use standard library for StringIO

# === Config ===
log_file = "log_full_dann.txt"
save_plot = "dann_training_plot.png"

# === Read log ===
with open(log_file) as f:
    lines = [line.strip() for line in f if not line.startswith("#") and line.strip()]
log_data = "\n".join(lines)
df = pd.read_csv(io.StringIO(log_data), sep="\t")

# === Plot ===
fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.set_title("DANN Training Log")
ax1.set_xlabel("Epoch")
ax1.plot(df["ep"], df["valAcc"], label="valAcc (%)", color="blue", marker="o")
ax1.plot(df["ep"], df["spAcc"], label="speciesAcc (%)", color="purple", linestyle="--")
ax1.set_ylabel("Accuracy (%)")
ax1.set_ylim(0, 100)
ax1.grid(True)

ax2 = ax1.twinx()
ax2.plot(df["ep"], df["trCE"], label="trCE", color="green")
ax2.plot(df["ep"], df["trDom"], label="trDom", color="red")
ax2.plot(df["ep"], df["valCE"], label="valCE", color="orange")
ax2.set_ylabel("Loss")

# === Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right")

plt.tight_layout()
plt.savefig(save_plot)
plt.show()
print("✅ Plot saved as:", save_plot)
