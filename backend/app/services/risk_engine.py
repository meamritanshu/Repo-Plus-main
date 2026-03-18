"""
risk_engine.py — Compute normalized risk scores for each file.

Risk Score = (Commit Frequency × 0.6) + (Total Churn × 0.4)
Both components are min-max normalized to [0, 1] before weighting.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

FREQ_WEIGHT = 0.6
CHURN_WEIGHT = 0.4


def compute_risk_scores(hotspot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a normalized risk score for every file.

    Args:
        hotspot_df: DataFrame from hotspot_calculator with columns
                    [file_path, commit_frequency, total_churn].

    Returns:
        DataFrame sorted by risk_score descending, with additional columns:
            norm_frequency, norm_churn, risk_score.
    """
    if hotspot_df.empty:
        return hotspot_df.copy()

    df = hotspot_df.copy()

    df["norm_frequency"] = _minmax(df["commit_frequency"])
    df["norm_churn"] = _minmax(df["total_churn"])

    df["risk_score"] = (
        df["norm_frequency"] * FREQ_WEIGHT + df["norm_churn"] * CHURN_WEIGHT
    ).round(4)

    df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    logger.info(f"Risk scores computed for {len(df)} files. Top file: {df.iloc[0]['file_path']}")
    return df


def _minmax(series: pd.Series) -> pd.Series:
    """Min-max normalize a pandas Series to [0, 1]."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)
