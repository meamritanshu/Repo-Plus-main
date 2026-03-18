"""
line_tracker.py — True line-level churn tracking engine.

For each commit, parses unified diffs to determine which line numbers
in the NEW version of each file were added or modified.
Accumulates modification counts across all commits.

Data structure returned:
    line_churn[file_path][str(line_number)] = modification_count
"""

import logging
import re
from collections import defaultdict

import git

logger = logging.getLogger(__name__)

# Regex for parsing unified diff hunk headers
# e.g. @@ -10,6 +10,8 @@ or @@ -0,0 +1 @@
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def track_line_churn(repo: git.Repo, commit_depth: int) -> dict[str, dict[str, int]]:
    """
    Walk commit history and track how many times each line was modified.

    Strategy:
    - Walk commits from newest to oldest (HEAD first).
    - For each commit that has a parent, compute the diff.
    - Parse the unified diff to extract NEW-version line numbers (the `+` lines).
    - Accumulate modification_count[file][line_number] for every touched line.

    Args:
        repo: GitPython Repo object.
        commit_depth: Maximum commits to process.

    Returns:
        dict[file_path, dict[str(line_no), count]]
    """
    # Use nested defaultdict
    line_churn: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    count = 0

    logger.info(f"Starting line-level churn tracking (depth={commit_depth})…")

    for commit in repo.iter_commits():
        if count >= commit_depth:
            break
        count += 1

        if not commit.parents:
            # First commit — all its lines are "new"
            try:
                for diff in commit.diff(git.NULL_TREE):
                    if diff.b_blob is None:
                        continue
                    file_path = diff.b_path
                    try:
                        raw_diff = diff.diff
                        if isinstance(raw_diff, bytes):
                            patch = raw_diff.decode("utf-8", errors="ignore")
                        else:
                            patch = raw_diff or ""
                        new_lines = _parse_added_lines(patch)
                        for ln in new_lines:
                            line_churn[file_path][str(ln)] += 1
                    except Exception:
                        pass
            except Exception:
                pass
            continue

        parent = commit.parents[0]
        try:
            diffs = parent.diff(commit, create_patch=True)
        except Exception:
            continue

        for diff in diffs:
            file_path = diff.b_path
            if file_path is None:
                continue

            try:
                raw_diff = diff.diff
                if isinstance(raw_diff, bytes):
                    patch = raw_diff.decode("utf-8", errors="ignore")
                else:
                    patch = raw_diff or ""

                if not patch:
                    continue

                new_lines = _parse_added_lines(patch)
                for ln in new_lines:
                    line_churn[file_path][str(ln)] += 1

            except Exception as e:
                logger.debug(f"Diff parse error for {file_path}: {e}")
                continue

    # Normalize to plain dicts for serialization
    result = {fp: dict(lines) for fp, lines in line_churn.items()}
    logger.info(f"Line churn tracked: {len(result)} files, {count} commits processed.")
    return result


def _parse_added_lines(patch: str) -> list[int]:
    """
    Parse a unified diff patch and return a list of NEW line numbers
    (in the post-commit / b-side version) that were added or modified.

    Only lines starting with '+' (not '+++') are counted.
    Context lines and deleted lines are skipped.

    Args:
        patch: Unified diff text.

    Returns:
        List of new-file line numbers that were added.
    """
    added_lines: list[int] = []
    current_new_line = 0

    for line in patch.splitlines():
        # Hunk header: extract new-file starting line number
        m = _HUNK_RE.match(line)
        if m:
            current_new_line = int(m.group(1))
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            # Added line — record its new-file line number
            added_lines.append(current_new_line)
            current_new_line += 1
        elif line.startswith("-"):
            # Deleted line — does NOT advance new-file counter
            pass
        elif line.startswith("\\"):
            # "No newline at end of file" marker — skip
            pass
        else:
            # Context line — both sides advance
            current_new_line += 1

    return added_lines


def compute_normalized_heatmap(
    line_churn_for_file: dict[str, int],
    total_lines: int,
) -> list[dict]:
    """
    Given a file's line churn dict and total current line count,
    build the full heatmap list (one entry per line).

    Args:
        line_churn_for_file: {str(line_no) -> count}
        total_lines: Number of lines in the current version of the file.

    Returns:
        List of dicts: [{line_number, modification_count, normalized_intensity}]
    """
    if not line_churn_for_file:
        return [
            {"line_number": i, "modification_count": 0, "normalized_intensity": 0.0}
            for i in range(1, total_lines + 1)
        ]

    max_count = max(line_churn_for_file.values(), default=1)
    if max_count == 0:
        max_count = 1

    result = []
    for ln in range(1, total_lines + 1):
        count = line_churn_for_file.get(str(ln), 0)
        intensity = round(count / max_count, 4)
        result.append({
            "line_number": ln,
            "modification_count": count,
            "normalized_intensity": intensity,
        })
    return result
