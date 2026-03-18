"""
developer_graph.py — Generate developer contribution bar chart.
"""

import logging
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)
DPI = 120


def plot_developer_contributions(dev_df: pd.DataFrame, out_dir: str, slug: str) -> str:
    """
    Generate a grouped/stacked bar chart showing developer contributions.

    Args:
        dev_df: Developer stats DataFrame from hotspot_calculator.
        out_dir: Output directory.
        slug: Repo slug.

    Returns:
        Filename of the saved chart.
    """
    if dev_df.empty:
        return ""

    top_devs = dev_df.head(15).copy()
    # Truncate long names
    top_devs["short_author"] = top_devs["author"].apply(lambda n: n[:20] + "…" if len(n) > 20 else n)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    x = range(len(top_devs))
    width = 0.35

    bars1 = ax.bar([i - width / 2 for i in x], top_devs["commit_count"],
                   width=width, label="Commits", color="#7c5cbf", alpha=0.9, edgecolor="none")
    bars2 = ax.bar([i + width / 2 for i in x], top_devs["files_touched"],
                   width=width, label="Files Touched", color="#00c9a7", alpha=0.9, edgecolor="none")

    ax.set_xticks(list(x))
    ax.set_xticklabels(top_devs["short_author"].values, rotation=35, ha="right",
                       color="#e0e0ff", fontsize=9)
    ax.set_ylabel("Count", color="#a0a0cc", fontsize=11)
    ax.set_title("👨‍💻 Developer Contributions", color="#ffffff", fontsize=14,
                 fontweight="bold", pad=15)

    legend = ax.legend(facecolor="#1a1a2e", edgecolor="#3a3a5e", labelcolor="#e0e0ff")
    ax.tick_params(colors="#a0a0cc")
    for spine in ax.spines.values():
        spine.set_color("#2a2a4a")

    plt.tight_layout()
    fname = f"{slug}_dev_graph.png"
    fig.savefig(os.path.join(out_dir, fname), dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info(f"Saved developer graph: {fname}")
    return fname
