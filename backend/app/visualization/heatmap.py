"""
heatmap.py — Generate a directory-level risk heatmap.
"""

import logging
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

logger = logging.getLogger(__name__)
DPI = 120


def plot_directory_heatmap(folder_df: pd.DataFrame, out_dir: str, slug: str) -> str:
    """
    Generate a seaborn heatmap showing commit frequency and churn per directory.

    Args:
        folder_df: Folder-level stats DataFrame from hotspot_calculator.
        out_dir: Output directory.
        slug: Repo slug for filename.

    Returns:
        Filename of the saved chart.
    """
    if folder_df.empty or len(folder_df) < 2:
        return ""

    top_folders = folder_df.head(20).copy()
    top_folders = top_folders.set_index("folder")

    # Select numeric columns for heatmap
    cols = [c for c in ["commit_frequency", "file_count", "total_churn"] if c in top_folders.columns]
    heat_data = top_folders[cols].copy()

    # Normalize each column independently for visual balance
    for col in cols:
        col_max = heat_data[col].max()
        if col_max > 0:
            heat_data[col] = heat_data[col] / col_max

    fig_height = max(5, len(top_folders) * 0.4 + 1.5)
    fig, ax = plt.subplots(figsize=(9, fig_height))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    sns.heatmap(
        heat_data,
        ax=ax,
        cmap="plasma",
        linewidths=0.5,
        linecolor="#0f0f1a",
        annot=True,
        fmt=".2f",
        annot_kws={"size": 8, "color": "white"},
        cbar_kws={"shrink": 0.8},
    )

    ax.set_title("🗂️ Directory Risk Heatmap (normalized)", color="#ffffff", fontsize=13,
                 fontweight="bold", pad=12)
    ax.set_xlabel("Metric", color="#a0a0cc", fontsize=10)
    ax.set_ylabel("Directory", color="#a0a0cc", fontsize=10)
    ax.tick_params(colors="#c0c0e0", labelsize=9)
    ax.set_xticklabels(cols, color="#c0c0e0", rotation=20, ha="right")

    plt.tight_layout()
    fname = f"{slug}_dir_heatmap.png"
    fig.savefig(os.path.join(out_dir, fname), dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info(f"Saved directory heatmap: {fname}")
    return fname
