"""Class-distribution chart for the report.

Run from backend/ (needs only matplotlib):
    python plot_class_distribution.py

Writes outputs/plots/class_distribution.png

The counts below are the three splits the models actually used: the dataset's train folder
(5,232 images) is split 85/15 (stratified, seed 42) into Train (4,447) and Validation (785) by
dataset.py, and the test folder (624 images) is left untouched. Edit the counts if your data changes.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- your counts: [NORMAL, PNEUMONIA] ---------------------------------------
COUNTS = {
    "Train": (1147, 3300),
    "Validation": (202, 583),
    "Test": (234, 390),
}
# -----------------------------------------------------------------------------

NORMAL_COLOR = "#2a78d6"     # blue
PNEUMONIA_COLOR = "#eb6834"  # orange
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"

HERE = Path(__file__).resolve().parent


def main():
    splits = list(COUNTS)
    normal = [COUNTS[s][0] for s in splits]
    pneu = [COUNTS[s][1] for s in splits]
    tot_n, tot_p = sum(normal), sum(pneu)
    total = tot_n + tot_p

    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    fig = plt.figure(figsize=(11, 5.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[4.2, 1.1], hspace=0.55)
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    # ---- top: images per split, by class ------------------------------------
    w = 0.36
    xs = range(len(splits))
    bn = ax.bar([x - w / 2 - 0.01 for x in xs], normal, w, color=NORMAL_COLOR, label="NORMAL")
    bp = ax.bar([x + w / 2 + 0.01 for x in xs], pneu, w, color=PNEUMONIA_COLOR, label="PNEUMONIA")
    for bars, vals in ((bn, normal), (bp, pneu)):
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 60, f"{v:,}", ha="center", va="bottom",
                    fontsize=10, color=INK)
    # ratio under each split label
    ratios = [p / n for n, p in zip(normal, pneu)]
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{s}\n{n + p:,} images · {r:.1f}:1" for s, n, p, r in zip(splits, normal, pneu, ratios)],
                       fontsize=10, color=INK_2)
    ax.set_ylim(0, max(pneu) * 1.14)
    ax.set_xlim(-0.6, len(splits) - 0.4)
    ax.set_ylabel("Number of images", color=INK_2, fontsize=10)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c3")
    ax.tick_params(axis="y", colors=INK_2, length=0)
    ax.tick_params(axis="x", length=0)
    ax.legend(frameon=False, loc="upper right", fontsize=10, ncol=2, bbox_to_anchor=(1.0, 1.08))
    ax.set_title("Chest X-ray dataset: images per split and class", loc="left", fontsize=13,
                 fontweight="bold", pad=14)

    # ---- bottom: overall share as one 100% bar ------------------------------
    ax2.barh([0], [tot_n], color=NORMAL_COLOR, height=0.55, edgecolor="white", linewidth=2)
    ax2.barh([0], [tot_p], left=[tot_n], color=PNEUMONIA_COLOR, height=0.55, edgecolor="white", linewidth=2)
    ax2.text(tot_n / 2, 0, f"NORMAL  {tot_n:,}  ({tot_n / total:.0%})", ha="center", va="center",
             color="white", fontsize=10, fontweight="bold")
    ax2.text(tot_n + tot_p / 2, 0, f"PNEUMONIA  {tot_p:,}  ({tot_p / total:.0%})", ha="center", va="center",
             color="white", fontsize=10, fontweight="bold")
    ax2.set_xlim(0, total)
    ax2.set_ylim(-0.5, 0.5)
    ax2.axis("off")
    ax2.set_title(f"All {total:,} images", loc="left", fontsize=10, color=INK_2, pad=2)

    fig.text(0.01, 0.01,
             "Ratio = PNEUMONIA : NORMAL. The classes are imbalanced, so training used class-weighted "
             "cross-entropy.\nTrain and Validation come from the dataset's training folder (85/15 stratified split); Test is the untouched test folder.",
             fontsize=8.5, color=INK_2, ha="left", va="bottom")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.9, bottom=0.14)

    out = HERE / "outputs" / "plots" / "class_distribution.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()