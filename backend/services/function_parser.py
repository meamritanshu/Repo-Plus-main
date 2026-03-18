"""
function_parser.py — Function/Method Boundary Detection

Supports:
    Python     (.py)             — ast.parse() → exact FunctionDef line ranges
    JavaScript (.js/.jsx/.ts)   — regex: declarations, class methods, arrows
    Java       (.java)           — regex: access modifier + return type + method

Returns list of:
    {
        "name":       str,
        "start_line": int,
        "end_line":   int,
        "language":   str,
    }

No external dependencies beyond stdlib.
"""

import ast
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Regex patterns for JavaScript / TypeScript
_JS_PATTERNS = [
    # Standard function declaration: function name(...)
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("),
    # Class method or object method: methodName(...) {
    re.compile(r"^\s+(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?(\w+)\s*\([^)]*\)\s*\{"),
    # Arrow function: const name = (...) => or const name = async (...) =>
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?"
               r"(?:\([^)]*\)|\w+)\s*=>"),
]

# Regex for Java methods
_JAVA_PATTERN = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final|synchronized|abstract|native|"
    r"default|transient|volatile)\s+)*"
    r"(?:(?:<[\w\s,<>\[\]?]+>\s+)?"  # generic return type
    r"[\w\[\]<>?.,\s]+\s+)"
    r"(\w+)\s*\("
)
_JAVA_SKIP = frozenset({"if", "for", "while", "switch", "catch", "try",
                         "else", "do", "return", "new", "class", "interface"})


def extract_functions(file_content: str, file_path: str) -> list:
    """
    Dispatch to language-specific parser based on file extension.

    Args:
        file_content: Full source code as string.
        file_path:    File path (used to determine language).

    Returns:
        List of { name, start_line, end_line, language }.
    """
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".py":
            return _parse_python(file_content)
        elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
            return _parse_javascript(file_content)
        elif ext == ".java":
            return _parse_java(file_content)
    except Exception as exc:
        logger.debug(f"function_parser: skipped {file_path}: {exc}")
    return []


# ── Python ────────────────────────────────────────────────────────────────────

def _parse_python(content: str) -> list:
    """
    Use ast.parse() for exact function boundaries (Python 3.8+ provides end_lineno).
    Falls back to start_line + rough estimate if end_lineno unavailable.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    funcs = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start = node.lineno
        end = getattr(node, "end_lineno", None)
        if end is None:
            # Estimate: scan forward from start to find dedent
            lines = content.splitlines()
            end = _estimate_end_line(lines, start - 1)
        funcs.append({
            "name":       node.name,
            "start_line": start,
            "end_line":   end,
            "language":   "python",
        })
    return funcs


# ── JavaScript / TypeScript ────────────────────────────────────────────────────

def _parse_javascript(content: str) -> list:
    """
    Regex-based function detection for JS/TS.
    Estimates end_line by tracking brace depth from the opening '{'.
    """
    lines = content.splitlines()
    funcs = []
    seen_names: set = set()

    for i, line in enumerate(lines):
        for pattern in _JS_PATTERNS:
            m = pattern.match(line)
            if not m:
                continue
            name = m.group(1)
            if name in ("if", "for", "while", "switch", "catch", "else", "return"):
                continue
            if name in seen_names:
                continue
            seen_names.add(name)
            end = _find_closing_brace(lines, i)
            funcs.append({
                "name":       name,
                "start_line": i + 1,      # 1-indexed
                "end_line":   end + 1,
                "language":   "javascript",
            })
            break

    return funcs


# ── Java ──────────────────────────────────────────────────────────────────────

def _parse_java(content: str) -> list:
    """
    Regex-based method detection for Java.
    Uses brace depth tracking to find method end.
    """
    lines = content.splitlines()
    funcs = []
    seen_names: set = set()

    for i, line in enumerate(lines):
        m = _JAVA_PATTERN.match(line)
        if not m:
            continue
        name = m.group(1)
        if name in _JAVA_SKIP or name in seen_names:
            continue
        # Make sure there's a '{' somewhere nearby
        context = " ".join(lines[i: i + 3])
        if "{" not in context:
            continue
        seen_names.add(name)
        end = _find_closing_brace(lines, i)
        funcs.append({
            "name":       name,
            "start_line": i + 1,
            "end_line":   end + 1,
            "language":   "java",
        })

    return funcs


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_closing_brace(lines: list, start_idx: int) -> int:
    """
    Starting from start_idx, scan forward to find the line where the opening
    brace is closed. Returns last line index (0-indexed). Falls back to
    start_idx + 50 if no matching brace found.
    """
    depth = 0
    found_open = False
    for i in range(start_idx, min(start_idx + 500, len(lines))):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                found_open = True
            elif ch == "}" and found_open:
                depth -= 1
                if depth == 0:
                    return i
    return min(start_idx + 50, len(lines) - 1)


def _estimate_end_line(lines: list, start_idx: int) -> int:
    """
    Estimate Python function end by finding the next line at the same or
    lower indentation level (after the def line).
    """
    if start_idx >= len(lines):
        return start_idx + 1
    def_line = lines[start_idx]
    base_indent = len(def_line) - len(def_line.lstrip())
    for i in range(start_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            continue
        cur_indent = len(lines[i]) - len(lines[i].lstrip())
        if cur_indent <= base_indent:
            return i  # exclusive; previous line was last of function
    return len(lines)


def aggregate_function_events(
    function_list: list,
    line_data: dict,
    window_ts: Optional[float] = None,
) -> list:
    """
    For each detected function, sum up modification events from line_data
    within the function's line range.

    Args:
        function_list: Output of extract_functions().
        line_data:     { line_str: { "count": int, "events": [[ts, author]] } }
        window_ts:     Optional Unix timestamp cutoff.

    Returns:
        List of function dicts enriched with instability metrics:
        {
            ...,
            "total_modifications": int,
            "total_churn":         int,
            "unique_contributors": int,
            "contributors":        list[str],
            "last_modified_ts":    float | None,
            "volatility":          float,
            "severity":            str,
        }
    """
    import math
    from datetime import datetime, timezone

    now_ts = datetime.now(tz=timezone.utc).timestamp()
    LAMBDA = 0.05

    results = []
    for fn in function_list:
        events_all = []
        for ln in range(fn["start_line"], fn["end_line"] + 1):
            ld = line_data.get(str(ln))
            if not ld:
                continue
            for ev in ld["events"]:
                if window_ts is None or ev[0] >= window_ts:
                    events_all.append(ev)

        contributors = list({e[1] for e in events_all})
        last_ts = max((e[0] for e in events_all), default=None)
        volatility = round(
            min(sum(math.exp(-LAMBDA * max(0.0, (now_ts - e[0]) / 86400))
                    for e in events_all) / max(len(events_all), 1), 1.0), 4
        ) if events_all else 0.0

        # Simple severity: 5 levels based on modification count
        count = len(events_all)
        if count == 0:      sev = "Stable"
        elif count < 5:     sev = "Mild"
        elif count < 15:    sev = "Moderate"
        elif count < 30:    sev = "Severe"
        else:               sev = "Critical"

        results.append({
            **fn,
            "total_modifications": count,
            "unique_contributors": len(contributors),
            "contributors":        contributors,
            "last_modified_ts":    last_ts,
            "volatility":          volatility,
            "severity":            sev,
        })

    # Sort by total_modifications descending (hottest functions first)
    results.sort(key=lambda x: x["total_modifications"], reverse=True)
    return results
