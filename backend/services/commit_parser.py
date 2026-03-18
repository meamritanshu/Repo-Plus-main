"""
commit_parser.py — Parse commit history into file-level metrics (plain dicts, no Pydantic).
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone

import git

logger = logging.getLogger(__name__)


def parse_commits(repo: git.Repo, commit_depth: int) -> dict:
    """
    Walk commit history and compute per-file metrics.
    Returns dict[file_path, dict] with plain Python dicts.
    """
    raw: dict = defaultdict(lambda: {
        "commit_hashes": set(),
        "ins": 0,
        "del": 0,
        "devs": defaultdict(lambda: {"commit_hashes": set(), "ins": 0, "del": 0}),
        "timeline": defaultdict(lambda: {"commits": 0, "churn": 0}),
        "last_date": None,
    })

    count = 0
    logger.info(f"Walking up to {commit_depth} commits...")

    for commit in repo.iter_commits():
        if count >= commit_depth:
            break
        count += 1
        try:
            stats = commit.stats.files
        except Exception:
            continue

        author = commit.author.name or "Unknown"
        ts = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)
        month_key = ts.strftime("%Y-%m")
        date_str = ts.strftime("%Y-%m-%d")

        for file_path, fdata in stats.items():
            ins = fdata.get("insertions", 0)
            dels = fdata.get("deletions", 0)
            r = raw[file_path]
            r["commit_hashes"].add(commit.hexsha[:8])
            r["ins"] += ins
            r["del"] += dels
            if r["last_date"] is None:
                r["last_date"] = date_str
            r["devs"][author]["commit_hashes"].add(commit.hexsha[:8])
            r["devs"][author]["ins"] += ins
            r["devs"][author]["del"] += dels
            r["timeline"][month_key]["commits"] += 1
            r["timeline"][month_key]["churn"] += ins + dels

    logger.info(f"Parsed {count} commits across {len(raw)} files.")

    result = {}
    for fp, r in raw.items():
        dev_stats = sorted([
            {
                "author": author,
                "commit_count": len(d["commit_hashes"]),
                "insertions": d["ins"],
                "deletions": d["del"],
            }
            for author, d in r["devs"].items()
        ], key=lambda x: x["commit_count"], reverse=True)[:10]

        timeline = [
            {"date": mk, "commits": v["commits"], "churn": v["churn"]}
            for mk, v in sorted(r["timeline"].items())
        ][-12:]

        churn = r["ins"] + r["del"]
        result[fp] = {
            "file_path": fp,
            "commit_count": len(r["commit_hashes"]),
            "insertions": r["ins"],
            "deletions": r["del"],
            "churn": churn,
            "risk_score": 0.0,
            "norm_frequency": 0.0,
            "norm_churn": 0.0,
            "developer_stats": dev_stats,
            "timeline": timeline,
            "last_commit_date": r["last_date"],
            "top_contributor": dev_stats[0]["author"] if dev_stats else None,
        }
    return result
