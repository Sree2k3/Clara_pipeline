#!/usr/bin/env python3
"""
compare_and_update.py

Usage:
    python scripts/compare_and_update.py <account_id> <v1_memo.json> <onboard.txt> <output_dir>

Example (run from the repository root):
    python scripts/compare_and_update.py demo_001 \
        outputs/accounts/demo_001/v1/memo.json \
        data/onboard/onboard_001.txt \
        outputs/accounts/demo_001
"""

import sys
import json
import os
from pathlib import Path
from deepdiff import DeepDiff

# ----------------------------------------------------------------------
# 1️⃣  Imports – note the **absolute** module paths
# ----------------------------------------------------------------------
# make sure the `scripts` folder is on the Python path (it already is when you run
# the script from the repo root, but we add a safety net)
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from scripts.extract_memo import extract_from_transcript  # absolute import
from scripts.render_agent_spec import render_spec  # absolute import
from deepdiff import DeepDiff


# ----------------------------------------------------------------------
# 2️⃣  Helper functions
# ----------------------------------------------------------------------
def load_json(p: Path):
    """Read a JSON file and return the Python dict."""
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"❌ Could not read JSON from {p}: {exc}") from exc


def save_json(p: Path, data: dict):
    """Write `data` as pretty‑printed JSON."""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def generate_changelog(diff: DeepDiff) -> str:
    """Turn DeepDiff output into a short markdown changelog."""
    if not diff:
        return "# Change Log\n\n*No changes detected.*\n"

    lines = ["# Change Log\n"]
    for change_type, changes in diff.items():
        if not changes:
            continue
        lines.append(f"## {change_type.replace('_', ' ').title()}\n")
        for path, detail in changes.items():
            # DeepDiff paths look like "root['field']['sub']"
            readable = (
                path.replace("root", "account")
                .replace("']['", ".")
                .replace("['", ".")
                .replace("']", "")
            )
            lines.append(f"- **{readable}** → {detail}\n")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# 3️⃣  Main routine
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) != 5:
        print(__doc__)  # print the usage docstring
        sys.exit(1)

    account_id, v1_memo_path_str, onboard_txt_path_str, out_dir_str = sys.argv[1:]

    v1_memo_path = Path(v1_memo_path_str)
    onboard_txt_path = Path(onboard_txt_path_str)
    out_dir = Path(out_dir_str)

    # ------------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------------
    if not v1_memo_path.is_file():
        raise FileNotFoundError(f"❌ v1 memo not found: {v1_memo_path}")

    if not onboard_txt_path.is_file():
        raise FileNotFoundError(
            f"❌ onboarding transcript not found: {onboard_txt_path}"
        )

    # ------------------------------------------------------------------
    # Load v1 memo
    # ------------------------------------------------------------------
    v1_memo = load_json(v1_memo_path)

    # ------------------------------------------------------------------
    # Extract onboarding memo (reuse the same extraction logic)
    # ------------------------------------------------------------------
    onboarding_text = onboard_txt_path.read_text(encoding="utf-8")
    onboarding_memo_obj = extract_from_transcript(onboarding_text, account_id)
    v2_memo = onboarding_memo_obj.model_dump(exclude_none=True)

    # ------------------------------------------------------------------
    # Compute the diff (DeepDiff gives us a nice structured change set)
    # ------------------------------------------------------------------
    diff = DeepDiff(v1_memo, v2_memo, ignore_order=True, report_repetition=True)

    # ------------------------------------------------------------------
    # Persist v2 memo
    # ------------------------------------------------------------------
    v2_memo_path = out_dir / "v2" / "memo.json"
    save_json(v2_memo_path, v2_memo)

    # ------------------------------------------------------------------
    # Write changelog (markdown)
    # ------------------------------------------------------------------
    changelog_md = generate_changelog(diff)
    changelog_path = out_dir / "v2" / "changes.md"
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    changelog_path.write_text(changelog_md, encoding="utf-8")

    # ------------------------------------------------------------------
    # Render v2 agent spec (using the same Jinja2 template as v1)
    # ------------------------------------------------------------------
    # The render function expects a *JSON file* that contains the memo.
    # We will write a temporary copy that the function can read.
    temp_json = out_dir / "v2" / "temp_memo.json"
    save_json(temp_json, v2_memo)

    v2_spec_path = out_dir / "v2" / "agent_spec.yaml"
    render_spec(temp_json, "v2", v2_spec_path)

    # Clean the temporary file (optional)
    try:
        temp_json.unlink()
    except Exception:
        pass

    # ------------------------------------------------------------------
    # Done – print a tiny summary
    # ------------------------------------------------------------------
    print(f"✅  v2 memo written to    : {v2_memo_path}")
    print(f"✅  v2 spec written to    : {v2_spec_path}")
    print(f"✅  changelog written to  : {changelog_path}")
    print("\n--- Diff summary ---")
    if diff:
        for change_type, changes in diff.items():
            print(f"{change_type}: {len(changes)} change(s)")
    else:
        print("No differences detected (v2 == v1).")


if __name__ == "__main__":
    main()
