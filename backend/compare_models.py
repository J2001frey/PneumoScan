"""Compare every model evaluated by evaluate.py.

Run from backend/ AFTER `python evaluate.py`:
    python compare_models.py

Reads  outputs/metrics.json
Writes outputs/model_comparison.csv          (table for the report)
       outputs/plots/model_comparison.png    (grouped bar chart)
Prints a Markdown table you can paste into the report.
Needs only matplotlib (no torch), so it runs in any environment.
"""
import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent

COLUMNS = [
    ("accuracy", "Accuracy"),
    ("recall_sensitivity", "Recall"),
    ("specificity", "Specificity"),
    ("precision", "Precision"),
    ("f1", "F1"),
    ("roc_auc", "AUC"),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--outputs", default=str(HERE / "outputs"))
    args = p.parse_args()
    out = Path(args.outputs)
    src = out / "metrics.json"
    if not src.exists():
        raise SystemExit(f"{src} not found. Run `python evaluate.py` first.")

    results = json.loads(src.read_text())
    if not results:
        raise SystemExit("metrics.json is empty.")

    names = sorted(results, key=lambda n: results[n]["f1"], reverse=True)

    rows = []
    for n in names:
        r = results[n]
        cm = r["confusion_matrix"]  # [[TN, FP], [FN, TP]]
        rows.append({
            "model": n,
            **{label: r[key] for key, label in COLUMNS},
            "False alarms (FP)": cm[0][1],
            "Missed pneumonia (FN)": cm[1][0],
            "ms/image": r["ms_per_image"],
            "Params (M)": r["parameters_millions"],
            "Size (MB)": r["file_size_mb"],
        })

    csv_path = out / "model_comparison.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Markdown table
    head = list(rows[0])
    print("| " + " | ".join(head) + " |")
    print("|" + "|".join(["---"] * len(head)) + "|")
    for row in rows:
        cells = []
        for k in head:
            v = row[k]
            if k == "model" or isinstance(v, int):
                cells.append(str(v))
            elif k in ("ms/image", "Params (M)", "Size (MB)"):
                cells.append(f"{v:.1f}")
            else:
                cells.append(f"{v:.3f}")
        print("| " + " | ".join(cells) + " |")

    # Grouped bar chart
    labels = [label for _, label in COLUMNS]
    n_models = len(names)
    width = 0.8 / n_models
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, n in enumerate(names):
        vals = [results[n][key] for key, _ in COLUMNS]
        xs = [j + (i - (n_models - 1) / 2) * width for j in range(len(labels))]
        bars = ax.bar(xs, vals, width, label=n)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.005, f"{v:.2f}",
                    ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    low = min(results[n][k] for n in names for k, _ in COLUMNS)
    ax.set_ylim(max(0.0, low - 0.1), 1.05)
    ax.set_ylabel("Score (test set)")
    ax.set_title("Model comparison on the test set")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=n_models, frameon=False)
    fig.tight_layout()
    png = out / "plots" / "model_comparison.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=150)
    plt.close(fig)

    best = names[0]
    print(f"\nBest F1: {best} ({results[best]['f1']:.3f})")
    fewest_fn = min(names, key=lambda n: results[n]["confusion_matrix"][1][0])
    print(f"Fewest missed pneumonia cases: {fewest_fn} "
          f"({results[fewest_fn]['confusion_matrix'][1][0]})")
    print(f"Saved -> {csv_path}")
    print(f"Saved -> {png}")


if __name__ == "__main__":
    main()
