"""
risk_engine.py — Compute normalized risk scores (plain dicts, no Pydantic).
"""
import logging

logger = logging.getLogger(__name__)

FREQ_WEIGHT = 0.6
CHURN_WEIGHT = 0.4


def compute_risk_scores(file_stats: dict) -> dict:
    """Mutate file_stats in-place, adding risk_score, norm_frequency, norm_churn."""
    if not file_stats:
        return file_stats

    freqs = [fs["commit_count"] for fs in file_stats.values()]
    churns = [fs["churn"] for fs in file_stats.values()]
    freq_min, freq_max = min(freqs), max(freqs)
    churn_min, churn_max = min(churns), max(churns)

    for fs in file_stats.values():
        nf = _norm(fs["commit_count"], freq_min, freq_max)
        nc = _norm(fs["churn"], churn_min, churn_max)
        fs["norm_frequency"] = round(nf, 4)
        fs["norm_churn"] = round(nc, 4)
        fs["risk_score"] = round(nf * FREQ_WEIGHT + nc * CHURN_WEIGHT, 4)

    logger.info(f"Risk scores computed for {len(file_stats)} files.")
    return file_stats


def _norm(value, min_val, max_val):
    if max_val == min_val:
        return 0.0
    return (value - min_val) / (max_val - min_val)
