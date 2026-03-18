import sys
import os
import logging
import json
import traceback
from pathlib import Path
from urllib.parse import unquote

# Ensure backend is on PYTHONPATH
BACKEND_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BACKEND_DIR))

from flask import Flask, request, jsonify, abort

# ── Services ──────────────────────────────────────────────
from services.repo_cloner import clone_repository
from services.commit_parser import parse_commits
from services.instability_engine import (
    analyze_instability, get_window_ts, filter_commit_events,
    filter_line_events, compute_volatility, compute_commit_volatility,
    compute_contributor_stats, compute_commit_contributor_stats,
    compute_smoothed_heatmap, compute_persistence,
    classify_severity, compute_combined_severity, compute_file_instability,
)
from services.function_parser import extract_functions, aggregate_function_events
from services.risk_engine import compute_risk_scores
import cache.store as store
import git

# ── Config ────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

TEMP_REPO_DIR = BACKEND_DIR / "data" / "temp_repos"
TEMP_REPO_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

# ── CORS (no flask-cors needed) ───────────────────────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route("/health", methods=["GET", "OPTIONS"])
def health():
    return jsonify({"status": "ok", "service": "RepoPulse API v2"})


# ── Tree builder ──────────────────────────────────────────
def _build_tree(file_stats: dict) -> dict:
    root = {"type": "folder", "name": "root", "path": "", "children": {}}
    for fp, fs in file_stats.items():
        parts = fp.replace("\\", "/").split("/")
        node = root
        cumulative = ""
        for i, part in enumerate(parts):
            cumulative = f"{cumulative}/{part}" if cumulative else part
            is_file = (i == len(parts) - 1)
            if is_file:
                node["children"][part] = {
                    "type": "file", "name": part, "path": fp,
                    "risk_score": round(fs.get("risk_score", 0), 4),
                    "commit_count": fs.get("commit_count", 0),
                    "churn": fs.get("churn", 0),
                    "top_contributor": fs.get("top_contributor"),
                    "last_commit_date": fs.get("last_commit_date"),
                }
            else:
                if part not in node["children"]:
                    node["children"][part] = {"type": "folder", "name": part, "path": cumulative, "children": {}}
                node = node["children"][part]
    return _dict_to_list(root)


def _dict_to_list(node):
    if "children" in node and isinstance(node["children"], dict):
        folders, files = [], []
        for child in node["children"].values():
            _dict_to_list(child)
            (folders if child.get("type") == "folder" else files).append(child)
        folders.sort(key=lambda x: x["name"])
        files.sort(key=lambda x: -x.get("risk_score", 0))
        node["children"] = folders + files
    return node


def _get_cached(repo_url):
    result = store.get(repo_url)
    if result is None:
        abort(404, description="Repository not analyzed yet. POST /analyze first.")
    return result


def _read_file(repo_path, file_path):
    full = Path(repo_path) / file_path
    if not full.exists():
        abort(404, description=f"File not found: {file_path}")
    try:
        return full.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        abort(500, description=f"Could not read file: {e}")


# ── Endpoints ─────────────────────────────────────────────

@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    body = request.get_json(force=True, silent=True) or {}
    repo_url = (body.get("repo_url") or "").strip().rstrip("/").replace(".git", "")
    commit_depth = int(body.get("commit_depth") or 200)

    if not repo_url.startswith("https://github.com/"):
        abort(422, description="Only https://github.com/ URLs are supported.")

    if store.has(repo_url):
        cached = store.get(repo_url)
        return jsonify({
            "status": "cached",
            "repo_url": repo_url,
            "commit_count": cached.get("commit_count", 0),
            "file_count": len(cached.get("file_stats", {})),
        })

    logger.info(f"Starting analysis: {repo_url} (depth={commit_depth})")
    try:
        repo_path = clone_repository(repo_url, str(TEMP_REPO_DIR))
        repo = git.Repo(repo_path)

        # File-level stats + risk scores
        file_stats = parse_commits(repo, commit_depth)
        compute_risk_scores(file_stats)
        commit_count = sum(1 for _ in repo.iter_commits(max_count=commit_depth))

        # Instability engine — single diff-parsing pass for timestamps + contributors
        logger.info("Running instability engine…")
        instability_data = analyze_instability(repo, commit_depth)

        # Derive simple line_churn dict for backward-compatible /file-line-heatmap
        line_churn = {
            fp: {ln: ld["count"] for ln, ld in lines.items()}
            for fp, lines in instability_data["line_data"].items()
        }

        store.set(repo_url, {
            "repo_url":        repo_url,
            "repo_path":       repo_path,
            "commit_count":    commit_count,
            "file_stats":      file_stats,
            "line_churn":      line_churn,
            "instability":     instability_data,
        })

        return jsonify({"status": "analyzed", "repo_url": repo_url,
                        "commit_count": commit_count, "file_count": len(file_stats)})

    except (ValueError, RuntimeError) as e:
        logger.error(f"Analysis error: {e}")
        abort(422, description=str(e))
    except Exception as e:
        logger.exception("Unexpected error")
        abort(500, description=f"Analysis failed: {e}")


@app.route("/repo-tree", methods=["GET"])
def repo_tree():
    from datetime import datetime, timezone
    repo_url = request.args.get("repo_url", "")
    window   = request.args.get("window", "all")
    result = _get_cached(repo_url)
    
    if window == "all":
        return jsonify(_build_tree(result["file_stats"]))
        
    inst = result.get("instability", {})
    window_ts = get_window_ts(window)
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    
    commit_events_map = inst.get("commit_events", {})
    filtered_stats = {}
    
    # We must iterate over original file_stats to ensure 0-churn files remain in the tree
    for fp, base_stat in result["file_stats"].items():
        events_all = commit_events_map.get(fp, [])
        filtered = filter_commit_events(events_all, window_ts)
        
        volatility = compute_commit_volatility(filtered, now_ts)
        churn = sum(e["insertions"] + e["deletions"] for e in filtered)
        severity = classify_severity(0.5 * min(len(filtered) / 100, 1.0) + 0.5 * volatility)
        
        filtered_stats[fp] = {
            "file_path": fp,
            "commit_count": len(filtered),
            "total_churn": churn,
            "volatility": volatility,
            "severity": severity,
        }
        
    return jsonify(_build_tree(filtered_stats))


@app.route("/workspace-status", methods=["GET"])
def workspace_status():
    from datetime import datetime
    repo_url = request.args.get("repo_url", "")
    if not repo_url:
        return jsonify({"active": False}), 400
    if store.has(repo_url):
        return jsonify({
            "active": True,
            "repo_id": repo_url,
            "timestamp": datetime.now().isoformat()
        })
    return jsonify({"active": False, "repo_id": repo_url})


@app.route("/file-content", methods=["GET"])
def file_content():
    repo_url = request.args.get("repo_url", "")
    path = unquote(request.args.get("path", ""))
    result = _get_cached(repo_url)
    content = _read_file(result["repo_path"], path)
    return jsonify({"path": path, "content": content})


@app.route("/file-metrics", methods=["GET"])
def file_metrics():
    repo_url = request.args.get("repo_url", "")
    path = unquote(request.args.get("path", ""))
    result = _get_cached(repo_url)
    fs = result["file_stats"].get(path)
    if fs is None:
        abort(404, description=f"No metrics for: {path}")
    return jsonify(fs)


@app.route("/file-line-heatmap", methods=["GET"])
def file_line_heatmap():
    repo_url = request.args.get("repo_url", "")
    path = unquote(request.args.get("path", ""))
    result = _get_cached(repo_url)
    line_churn_file = result["line_churn"].get(path, {})
    try:
        content = _read_file(result["repo_path"], path)
        total_lines = len(content.splitlines())
    except Exception:
        total_lines = max((int(k) for k in line_churn_file), default=0)
    return jsonify(compute_normalized_heatmap(line_churn_file, total_lines))


# ── Hotspot Endpoints ────────────────────────────────────────────────────────

def _get_instability(repo_url: str) -> dict:
    result = _get_cached(repo_url)
    inst = result.get("instability")
    if inst is None:
        abort(404, description="Instability data not found. POST /analyze first.")
    return inst


@app.route("/hotspots/file", methods=["GET"])
def hotspot_file():
    """
    GET /hotspots/file?repo_url=&path=&window=all

    Returns comprehensive instability metrics for a single file:
    - commit count, total churn, insertions/deletions
    - volatility (exponential decay)
    - contributor concentration
    - hotspot persistence (monthly buckets)
    - severity classification (Stable → Critical)
    """
    repo_url = request.args.get("repo_url", "")
    path     = unquote(request.args.get("path", ""))
    window   = request.args.get("window", "all")
    inst     = _get_instability(repo_url)
    report   = compute_file_instability(path, inst, window)
    return jsonify(report)


@app.route("/hotspots/function", methods=["GET"])
def hotspot_function():
    """
    GET /hotspots/function?repo_url=&path=&window=all

    Returns function-level instability ranking for the given file:
    each function shows total_modifications, unique_contributors,
    volatility, and severity. Sorted hottest-first.
    """
    repo_url = request.args.get("repo_url", "")
    path     = request.args.get("path", "")
    window   = request.args.get("window", "all")
    result   = _get_cached(repo_url)
    inst     = result.get("instability", {})
    window_ts = get_window_ts(window)

    # Read file content for function parsing
    try:
        content = _read_file(result["repo_path"], path)
    except Exception:
        content = ""

    line_data = inst.get("line_data", {}).get(path, {})
    fns = extract_functions(content, path)
    enriched = aggregate_function_events(fns, line_data, window_ts)

    return jsonify({
        "file_path":        path,
        "window":           window,
        "function_count":   len(enriched),
        "functions":        enriched,
    })


@app.route("/hotspots/line", methods=["GET"])
def hotspot_line():
    """
    GET /hotspots/line?repo_url=&path=&window=all

    Returns per-line heatmap with:
    - modification_count, normalized_intensity  (raw)
    - block_id, block_churn, block_intensity    (smoothed, 10-line blocks)
    - contributor_count, last_modified_ts
    - severity per line (Stable → Critical)
    """
    repo_url = request.args.get("repo_url", "")
    path     = request.args.get("path", "")
    window   = request.args.get("window", "all")
    result   = _get_cached(repo_url)
    inst     = result.get("instability", {})
    window_ts = get_window_ts(window)

    line_data_all = inst.get("line_data", {}).get(path, {})
    line_data = filter_line_events(line_data_all, window_ts)

    # Get total line count from file
    try:
        content = _read_file(result["repo_path"], path)
        total_lines = len(content.splitlines())
    except Exception:
        total_lines = max((int(k) for k in line_data if k.isdigit()), default=0)

    heatmap = compute_smoothed_heatmap(line_data, total_lines)
    return jsonify({
        "file_path":   path,
        "window":      window,
        "total_lines": total_lines,
        "heatmap":     heatmap,
    })


@app.route("/hotspots/time-filter", methods=["GET"])
def hotspot_time_filter():
    """
    GET /hotspots/time-filter?repo_url=&window=30d

    Re-ranks ALL files by instability within the specified time window.
    Returns top 20 files with their re-computed metrics.
    Windows: 30d | 90d | 1y | all
    """
    from datetime import datetime, timezone
    repo_url = request.args.get("repo_url", "")
    window   = request.args.get("window", "30d")
    inst     = _get_instability(repo_url)
    window_ts = get_window_ts(window)
    now_ts   = datetime.now(tz=timezone.utc).timestamp()

    ranked = []
    commit_events_map = inst.get("commit_events", {})
    for fp, events_all in commit_events_map.items():
        filtered = filter_commit_events(events_all, window_ts)
        if not filtered:
            continue
        volatility = compute_commit_volatility(filtered, now_ts)
        churn = sum(e["insertions"] + e["deletions"] for e in filtered)
        contrib = compute_commit_contributor_stats(filtered)
        persistence = compute_persistence(events_all, window_ts)
        severity = classify_severity(0.5 * min(len(filtered) / 100, 1.0) + 0.5 * volatility)
        ranked.append({
            "file_path":         fp,
            "commit_count":      len(filtered),
            "total_churn":       churn,
            "volatility":        volatility,
            "contributor_stats": contrib,
            "persistence":       persistence,
            "severity":          severity,
        })

    ranked.sort(key=lambda x: x["volatility"], reverse=True)
    return jsonify({
        "window":     window,
        "file_count": len(ranked),
        "files":      ranked[:20],
    })


@app.route("/hotspots/summary", methods=["GET"])
def hotspot_summary():
    """
    GET /hotspots/summary?repo_url=

    Repo-wide instability snapshot:
    - Top 10 hotspot files
    - Severity distribution across all files
    - Most volatile contributors
    - Total tracked lines, total events
    """
    from datetime import datetime, timezone
    repo_url = request.args.get("repo_url", "")
    result   = _get_cached(repo_url)
    inst     = result.get("instability", {})
    now_ts   = datetime.now(tz=timezone.utc).timestamp()

    commit_events_map = inst.get("commit_events", {})
    line_data_map     = inst.get("line_data", {})

    severity_dist = {"Stable": 0, "Mild": 0, "Moderate": 0, "Severe": 0, "Critical": 0}
    contributor_counts: dict = {}
    ranked = []
    total_line_events = 0

    for fp, events_all in commit_events_map.items():
        volatility = compute_commit_volatility(events_all, now_ts)
        churn      = sum(e["insertions"] + e["deletions"] for e in events_all)
        severity   = classify_severity(0.5 * min(len(events_all) / 100, 1.0) + 0.5 * volatility)
        severity_dist[severity] = severity_dist.get(severity, 0) + 1

        for e in events_all:
            contributor_counts[e["author"]] = contributor_counts.get(e["author"], 0) + 1

        ranked.append({"file_path": fp, "churn": churn,
                       "volatility": volatility, "severity": severity})

    for lines in line_data_map.values():
        for ld in lines.values():
            total_line_events += ld.get("count", 0)

    ranked.sort(key=lambda x: x["volatility"], reverse=True)
    top_contributors = sorted(contributor_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return jsonify({
        "repo_url":           repo_url,
        "total_files":        len(commit_events_map),
        "total_line_events":  total_line_events,
        "severity_distribution": severity_dist,
        "top_hotspot_files":  ranked[:10],
        "top_contributors":   [{"author": a, "commit_count": c} for a, c in top_contributors],
    })


# ── Error handlers ────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e)}), 404

@app.errorhandler(422)
def unprocessable(e):
    return jsonify({"detail": str(e.description)}), 422

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": str(e.description)}), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  RepoPulse API v2 — Flask Backend")
    print("=" * 55)
    print(f"  Backend dir : {BACKEND_DIR}")
    print(f"  API running at: http://localhost:8000")
    print(f"  Health check:   http://localhost:8000/health")
    print()
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=True)
