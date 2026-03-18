"""
instability_engine.py — Code Instability Intelligence Engine

Computes:
  1. Line-level churn with timestamps and contributors
  2. Volatility with exponential decay weighting
  3. Contributor concentration
  4. Heatmap smoothing (raw + 10-line block aggregation)
  5. Hotspot persistence (monthly bucket analysis)
  6. Instability severity classification (Stable → Critical)

This module is data-only: no recommendations, no AI reasoning.
"""

import math
import re
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional

import git

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
LAMBDA_DECAY = 0.05   # Exponential decay rate per day (half-life ≈ 14 days)
BLOCK_SIZE = 10       # Lines per smoothing block

SEVERITY_BANDS = [
    (0.20, "Stable"),
    (0.40, "Mild"),
    (0.60, "Moderate"),
    (0.80, "Severe"),
    (1.01, "Critical"),
]


# ── Main Analysis Pass ────────────────────────────────────────────────────────

def analyze_instability(repo: git.Repo, commit_depth: int) -> dict:
    """
    Single diff-parsing pass across commit history.

    Returns:
        {
          "line_data":      { file_path: { line_str: { "count": int, "events": [[ts, author]] } } },
          "commit_events":  { file_path: [ { "ts", "author", "insertions", "deletions" } ] }
        }

    This is a superset of simple line_churn — callers can derive
    line_churn = { fp: { ln: d["count"] } } for backward compatibility.
    """
    line_data: dict = defaultdict(lambda: defaultdict(lambda: {"count": 0, "events": []}))
    commit_events: dict = defaultdict(list)

    count = 0
    logger.info(f"Instability analysis started (depth={commit_depth})…")

    for commit in repo.iter_commits():
        if count >= commit_depth:
            break
        count += 1

        ts = float(commit.committed_date)
        author = commit.author.name or "Unknown"

        if not commit.parents:
            # Initial commit — treat all added lines as new
            try:
                for diff in commit.diff(git.NULL_TREE):
                    if diff.b_blob is None:
                        continue
                    raw = diff.diff
                    patch = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else (raw or "")
                    _parse_patch(patch, diff.b_path, ts, author, line_data, commit_events)
            except Exception:
                pass
            continue

        parent = commit.parents[0]
        try:
            diffs = parent.diff(commit, create_patch=True)
        except Exception:
            continue

        for diff in diffs:
            fp = diff.b_path
            if not fp:
                continue
            try:
                raw = diff.diff
                patch = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else (raw or "")
                if patch:
                    _parse_patch(patch, fp, ts, author, line_data, commit_events)
            except Exception:
                continue

    logger.info(f"Instability done: {count} commits, {len(line_data)} files tracked.")
    return {
        "line_data":     {fp: dict(lines) for fp, lines in line_data.items()},
        "commit_events": dict(commit_events),
    }


def _parse_patch(patch: str, file_path: str, ts: float, author: str,
                 line_data: dict, commit_events: dict) -> None:
    """Parse unified diff and update per-line event tracking."""
    current_line = 0
    ins = dels = 0

    for line in patch.splitlines():
        m = HUNK_RE.match(line)
        if m:
            current_line = int(m.group(1))
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            ld = line_data[file_path][str(current_line)]
            ld["count"] += 1
            ld["events"].append([ts, author])
            ins += 1
            current_line += 1
        elif line.startswith("-"):
            dels += 1
        elif not line.startswith("\\"):
            current_line += 1

    if ins + dels > 0:
        commit_events[file_path].append({
            "ts": ts, "author": author,
            "insertions": ins, "deletions": dels,
        })


# ── Time Filtering ────────────────────────────────────────────────────────────

def get_window_ts(window: str) -> Optional[float]:
    """
    Return the Unix timestamp for the START of the requested window.
    Returns None for "all" (no filtering).
    """
    now = datetime.now(tz=timezone.utc)
    mapping = {
        "30d":  timedelta(days=30),
        "90d":  timedelta(days=90),
        "6m":   timedelta(days=180),
        "all":  None,
    }
    delta = mapping.get(window.lower())
    return (now - delta).timestamp() if delta else None


def filter_line_events(line_data: dict, window_ts: Optional[float]) -> dict:
    """Return a copy of line_data with events filtered to the time window."""
    if window_ts is None:
        return line_data
    result = {}
    for ln_str, ld in line_data.items():
        filtered = [e for e in ld["events"] if e[0] >= window_ts]
        if filtered:
            result[ln_str] = {"count": len(filtered), "events": filtered}
    return result


def filter_commit_events(events: list, window_ts: Optional[float]) -> list:
    """Filter a list of commit event dicts by timestamp."""
    if window_ts is None:
        return events
    return [e for e in events if e["ts"] >= window_ts]


# ── Volatility ────────────────────────────────────────────────────────────────

def compute_volatility(events: list, now_ts: float) -> float:
    """
    Volatility with exponential decay weighting.

    weight(event) = exp(-λ × age_in_days)
    volatility    = Σ(weights) / total_events      (normalized 0–1)

    Events: list of [ts, author] pairs.
    """
    if not events:
        return 0.0
    total_weight = sum(
        math.exp(-LAMBDA_DECAY * max(0.0, (now_ts - e[0]) / 86400))
        for e in events
    )
    # Normalize: max theoretical = len(events) (all events happening NOW)
    return round(min(total_weight / max(len(events), 1), 1.0), 4)


def compute_commit_volatility(commit_events: list, now_ts: float) -> float:
    """Same as compute_volatility but for commit-event dicts."""
    if not commit_events:
        return 0.0
    total_weight = sum(
        math.exp(-LAMBDA_DECAY * max(0.0, (now_ts - e["ts"]) / 86400))
        for e in commit_events
    )
    return round(min(total_weight / max(len(commit_events), 1), 1.0), 4)


# ── Contributor Concentration ─────────────────────────────────────────────────

def compute_contributor_stats(events: list) -> dict:
    """
    Contributor concentration for a set of events [[ts, author], ...].

    concentration = unique_contributors / total_modifications
    High count (>20) + high concentration (>0.5): unstable collaboration zone.
    """
    if not events:
        return {
            "unique_contributors": 0, "total_modifications": 0,
            "concentration": 0.0, "contributors": [],
            "is_unstable_zone": False,
        }
    contributors = list({e[1] for e in events})
    total = len(events)
    unique = len(contributors)
    concentration = round(unique / max(total, 1), 4)
    return {
        "unique_contributors": unique,
        "total_modifications": total,
        "concentration": concentration,
        "contributors": contributors,
        "is_unstable_zone": bool(total > 20 and concentration > 0.5),
    }


def compute_commit_contributor_stats(commit_events: list) -> dict:
    """Same as above but for commit-event dicts {ts, author, ins, dels}."""
    if not commit_events:
        return {"unique_contributors": 0, "total_modifications": 0,
                "concentration": 0.0, "contributors": [], "is_unstable_zone": False}
    contributors = list({e["author"] for e in commit_events})
    total = len(commit_events)
    unique = len(contributors)
    concentration = round(unique / max(total, 1), 4)
    return {
        "unique_contributors": unique,
        "total_modifications": total,
        "concentration": concentration,
        "contributors": contributors,
        "is_unstable_zone": bool(total > 20 and concentration > 0.5),
    }


# ── Heatmap Smoothing ─────────────────────────────────────────────────────────

def compute_smoothed_heatmap(line_data: dict, total_lines: int,
                              block_size: int = BLOCK_SIZE) -> list:
    from datetime import datetime, timezone
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    
    total_lines = max(total_lines, 1)
    max_count = max((d["count"] for d in line_data.values()), default=1) or 1

    # Pre-compute block metrics
    blocks_churn: dict = defaultdict(int)
    blocks_vol: dict = defaultdict(float)
    blocks_recency: dict = defaultdict(float)
    
    line_metrics = {}
    for ln_str, d in line_data.items():
        try:
            ln = int(ln_str)
            block_id = (ln - 1) // block_size
            events = d.get("events", [])
            
            # Line Churn
            blocks_churn[block_id] += d["count"]
            
            # Line Volatility
            vol = compute_volatility(events, now_ts)
            blocks_vol[block_id] += vol
            
            # Line Recency
            last_ts = max((e[0] for e in events), default=None)
            recency = 0.0
            if last_ts:
                age_days = max(0.0, (now_ts - last_ts) / 86400)
                recency = math.exp(-LAMBDA_DECAY * age_days)
            blocks_recency[block_id] = max(blocks_recency[block_id], recency)
            
            line_metrics[ln] = {
                "count": d["count"],
                "events": events,
                "vol": vol,
                "recency": recency,
                "last_ts": last_ts
            }
        except (ValueError, TypeError):
            pass

    max_block_churn = max(blocks_churn.values(), default=1) or 1
    max_block_vol = max(blocks_vol.values(), default=1.0) or 1.0

    result = []
    for ln in range(1, total_lines + 1):
        metrics = line_metrics.get(ln, {})
        count = metrics.get("count", 0)
        events = metrics.get("events", [])
        vol = metrics.get("vol", 0.0)
        recency = metrics.get("recency", 0.0)
        last_ts = metrics.get("last_ts", None)
        
        block_id = (ln - 1) // block_size
        block_churn = blocks_churn.get(block_id, 0)
        block_vol = blocks_vol.get(block_id, 0.0)
        block_recency = blocks_recency.get(block_id, 0.0)
        
        norm = round(count / max_count, 4)
        severity = classify_severity(norm)

        result.append({
            "line_number":          ln,
            "modification_count":   count,
            "normalized_intensity": norm,
            "line_volatility":      round(vol, 4),
            "recency_score":        round(recency, 4),
            
            "block_id":             block_id,
            "block_churn":          block_churn,
            "block_intensity":      round(block_churn / max_block_churn, 4),
            "block_volatility":     round(block_vol / max_block_vol, 4),
            "block_recency":        round(block_recency, 4),
            
            "contributor_count":    len({e[1] for e in events}),
            "last_modified_ts":     last_ts,
            "severity":             severity,
        })
    return result


# ── Persistence ───────────────────────────────────────────────────────────────

def compute_persistence(commit_events: list, window_ts: Optional[float] = None) -> dict:
    """
    Split history into monthly time buckets and measure hotspot persistence.

    Returns:
        {
          "active_buckets":       int,   # months with any activity
          "total_buckets":        int,
          "persistence_ratio":    float, # 0–1
          "classification":       str,   # Chronic / Recurrent / Temporary Spike
        }

    Chronic (>60%): sustained instability across most of history
    Recurrent (30–60%): periodic instability
    Temporary Spike (<30%): isolated bursts
    """
    filtered = [e for e in commit_events
                if window_ts is None or e["ts"] >= window_ts]
    if not filtered:
        return {"active_buckets": 0, "total_buckets": 0,
                "persistence_ratio": 0.0, "classification": "Stable"}

    active_months: set = set()
    for e in filtered:
        dt = datetime.fromtimestamp(e["ts"], tz=timezone.utc)
        active_months.add((dt.year, dt.month))

    ts_vals = [e["ts"] for e in filtered]
    span_days = (max(ts_vals) - min(ts_vals)) / 86400
    total_buckets = max(1, int(span_days / 30) + 1)
    active = len(active_months)
    ratio = round(active / total_buckets, 4)

    if ratio > 0.60:
        classification = "Chronic"
    elif ratio > 0.30:
        classification = "Recurrent"
    else:
        classification = "Temporary Spike"

    return {
        "active_buckets":    active,
        "total_buckets":     total_buckets,
        "persistence_ratio": ratio,
        "classification":    classification,
    }


# ── Severity Classification ───────────────────────────────────────────────────

def classify_severity(normalized_score: float) -> str:
    """
    Classify an instability metric (0–1) into a severity label.

    0.00 – 0.20  → Stable
    0.20 – 0.40  → Mild
    0.40 – 0.60  → Moderate
    0.60 – 0.80  → Severe
    0.80 – 1.00  → Critical
    """
    for threshold, label in SEVERITY_BANDS:
        if normalized_score < threshold:
            return label
    return "Critical"


def compute_combined_severity(churn: int, volatility: float, all_churns: list) -> dict:
    """
    Combined severity using normalized churn rank + volatility.
    Returns {"score": float, "severity": str}
    """
    max_churn = max(all_churns) if all_churns else 1
    norm_churn = churn / max(max_churn, 1)
    combined = round(0.5 * norm_churn + 0.5 * volatility, 4)
    return {"score": combined, "severity": classify_severity(combined)}


# ── File Instability Summary ──────────────────────────────────────────────────

def compute_file_instability(file_path: str, instability_data: dict,
                              window: str = "all") -> dict:
    """
    Full instability report for a single file at the given time window.
    Used by /hotspots/file endpoint.
    """
    from datetime import datetime, timezone
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    window_ts = get_window_ts(window)

    line_data_all = instability_data["line_data"].get(file_path, {})
    commit_events_all = instability_data["commit_events"].get(file_path, [])

    # Apply time filter
    line_data = filter_line_events(line_data_all, window_ts)
    commit_events = filter_commit_events(commit_events_all, window_ts)

    all_events = [e for ld in line_data.values() for e in ld["events"]]

    total_churn = sum(e["insertions"] + e["deletions"] for e in commit_events)
    volatility = compute_commit_volatility(commit_events, now_ts)
    contributor_stats = compute_commit_contributor_stats(commit_events)
    persistence = compute_persistence(commit_events_all, window_ts)
    
    # Calculate global max churn for relative severity scoring
    max_churn = 1
    all_commit_events = instability_data.get("commit_events", {})
    for f_events in all_commit_events.values():
        f_filtered = filter_commit_events(f_events, window_ts)
        file_churn = sum(e["insertions"] + e["deletions"] for e in f_filtered)
        if file_churn > max_churn:
            max_churn = file_churn
            
    norm_churn = total_churn / max_churn
    combined = 0.5 * norm_churn + 0.5 * volatility
    severity = classify_severity(combined)

    # Calculate Dev Stats & Churn
    dev_counts = defaultdict(int)
    for e in commit_events:
        dev_counts[e["author"]] += e["insertions"] + e["deletions"]
    
    devStats = [{"author": k, "commit_count": v} for k, v in sorted(dev_counts.items(), key=lambda x: x[1], reverse=True)]
    top_dev_pct = 0
    if total_churn > 0 and devStats:
        top_dev_pct = round((devStats[0]["commit_count"] / total_churn) * 100)

    # Calculate Timeline
    tl = defaultdict(lambda: {"churn": 0, "commits": 0})
    for e in commit_events:
        try:
            dt = datetime.fromtimestamp(e["ts"], tz=timezone.utc)
            k = dt.strftime("%Y-%m")
            tl[k]["churn"] += e["insertions"] + e["deletions"]
            tl[k]["commits"] += 1
        except Exception:
            pass
    timeline = [{"date": k, "churn": v["churn"], "commits": v["commits"]} for k, v in sorted(tl.items())]

    return {
        "file_path":          file_path,
        "window":             window,
        "commit_count":       len(commit_events),
        "total_churn":        total_churn,
        "insertions":         sum(e["insertions"] for e in commit_events),
        "deletions":          sum(e["deletions"] for e in commit_events),
        "volatility":         volatility,
        "line_count_tracked": len(line_data),
        "contributor_stats":  contributor_stats,
        "persistence":        persistence,
        "severity":           severity,
        "devStats":           devStats,
        "top_contributor":    devStats[0]["author"] if devStats else "Unknown",
        "timeline":           timeline,
        "top_dev_pct":        top_dev_pct,
    }
