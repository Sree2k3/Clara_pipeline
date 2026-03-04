#!/usr/bin/env python3
"""
render_agent_spec.py

Usage (called by other scripts):
    render_spec(<memo_json_path>, <version>, <out_path>)

All three arguments can be either pathlib.Path objects or ordinary strings.
"""

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def render_spec(memo_json_path, version: str, out_path):
    """
    Render a Retell agent specification (YAML) from an account memo.

    Parameters
    ----------
    memo_json_path : Union[str, Path]
        Path to the JSON file that contains the memo (v1 or v2).
    version : str
        `"v1"` or `"v2"` – will be injected into the template.
    out_path : Union[str, Path]
        Destination file for the rendered YAML (or JSON).

    The function writes the rendered file and prints a short success message.
    """
    # ---- Normalise arguments to pathlib.Path objects -------------------
    memo_path = (
        Path(memo_json_path) if not isinstance(memo_json_path, Path) else memo_json_path
    )
    out_path = Path(out_path) if not isinstance(out_path, Path) else out_path

    # ---- Load the memo ------------------------------------------------
    try:
        memo = json.loads(memo_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"❌ Could not read memo JSON from {memo_path}: {exc}"
        ) from exc

    # ---- Jinja2 template rendering -----------------------------------
    env = Environment(
        loader=FileSystemLoader("templates"), trim_blocks=True, lstrip_blocks=True
    )
    template = env.get_template("agent_spec.yaml.j2")
    rendered = template.render(memo=memo, version=version)

    # ---- Write the output ---------------------------------------------
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    print(f"✅  Agent spec ({version}) written to {out_path}")


# ----------------------------------------------------------------------
# Allow the script to be run directly for ad‑hoc testing
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    render_spec(sys.argv[1], sys.argv[2], sys.argv[3])
