"""
churn_chart.py — Generate churn-related visualizations.
"""

import logging
import os

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

PALETTE = "viridis"
DPI = 120


def plot_top_files_by_risk(risk_df: pd.DataFrame, out_dir: str, slug: str) -> str:
    """
    Generate a horizontal bar chart of the top 15 files by risk score.

    Args:
        risk_df: Ranked DataFrame from risk_engine.
        out_dir: Directory to save the chart.
        slug: Repo slug used in the filename.

    Returns:
        Filename (not full path) of the saved chart.
    """
    if risk_df.empty:
        return ""

    top = risk_df.head(15).copy()
    top["short_name"] = top["file_path"].apply(lambda p: p.split("/")[-1] if "/" in p else p)

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    colors = sns.color_palette("plasma", len(top))[::-1]
    bars = ax.barh(range(len(top)), top["risk_score"].values, color=colors, edgecolor="none", height=0.65)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["short_name"].values, fontsize=9, color="#e0e0ff")
    ax.invert_yaxis()

    ax.set_xlabel("Risk Score", color="#a0a0cc", fontsize=11)
    ax.set_title("🔥 Top 15 High-Risk Files", color="#ffffff", fontsize=14, fontweight="bold", pad=15)

    ax.tick_params(colors="#a0a0cc")
    for spine in ax.spines.values():
        spine.set_color("#2a2a4a")
    ax.xaxis.label.set_color("#a0a0cc")

    # Value labels on bars
    for bar, val in zip(bars, top["risk_score"].values):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", color="#c8c8ff", fontsize=8)

    plt.tight_layout()
    fname = f"{slug}_risk_bar.png"
    fig.savefig(os.path.join(out_dir, fname), dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info(f"Saved risk bar chart: {fname}")
    return fname


def plot_churn_distribution(hotspot_df: pd.DataFrame, out_dir: str, slug: str) -> str:
    """
    Generate a churn distribution histogram.

    Args:
        hotspot_df: File-level hotspot DataFrame.
        out_dir: Output directory.
        slug: Repo slug.

    Returns:
        Filename of the saved chart.
    """
    if hotspot_df.empty:
        return ""

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    churn = hotspot_df["total_churn"].clip(upper=hotspot_df["total_churn"].quantile(0.95))
    ax.hist(churn, bins=30, color="#7c5cbf", edgecolor="#0f0f1a", alpha=0.85)

    ax.set_xlabel("Total Churn (lines changed)", color="#a0a0cc", fontsize=11)
    ax.set_ylabel("Number of Files", color="#a0a0cc", fontsize=11)
    ax.set_title("📊 File Churn Distribution", color="#ffffff", fontsize=14, fontweight="bold", pad=15)

    ax.tick_params(colors="#a0a0cc")
    for spine in ax.spines.values():
        spine.set_color("#2a2a4a")

    plt.tight_layout()
    fname = f"{slug}_churn_dist.png"
    fig.savefig(os.path.join(out_dir, fname), dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info(f"Saved churn distribution chart: {fname}")
    return fname
