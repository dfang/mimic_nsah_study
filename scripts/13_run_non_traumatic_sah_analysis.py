#!/usr/bin/env python3
"""Run the non-traumatic SAH phenotype analysis script from a terminal.

The analysis file was authored for BigQuery Notebook/Colab-style execution and
uses display(). This wrapper provides a terminal-safe display() implementation
and then executes the existing analysis script unchanged.
"""

from __future__ import annotations

import argparse
import builtins
import os
import runpy
import sys
from pathlib import Path
from typing import Any


DEFAULT_ANALYSIS_FILE = "11_bigquery_notebook_non_traumatic_sah_analysis.py"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def terminal_display(obj: Any = None, **_: Any) -> None:
    """Minimal display() replacement for normal Python execution."""
    if obj is None:
        return
    if hasattr(obj, "to_string"):
        print(obj.to_string())
        return
    print(obj)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run 11_bigquery_notebook_non_traumatic_sah_analysis.py locally."
    )
    parser.add_argument(
        "--analysis-file",
        default=DEFAULT_ANALYSIS_FILE,
        help=f"Python analysis file to run. Default: {DEFAULT_ANALYSIS_FILE}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analysis_path = Path(args.analysis_file)

    os.environ.setdefault("MPLBACKEND", "Agg")
    builtins.display = terminal_display
    if str(REPOSITORY_ROOT) not in sys.path:
        sys.path.insert(0, str(REPOSITORY_ROOT))

    print(f"Analysis file: {analysis_path}")
    runpy.run_path(str(analysis_path), run_name="__main__")


if __name__ == "__main__":
    main()
