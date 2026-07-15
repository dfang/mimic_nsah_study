"""Shared command-line compatibility for canonical artifact generators."""

from __future__ import annotations

import re
import sys


def accept_legacy_date_arg(args: list[str], program: str) -> None:
    """Accept one deprecated YYYYMMDD argument without changing output paths."""
    if not args:
        return
    if len(args) == 1 and re.fullmatch(r"\d{8}", args[0]):
        print(
            f"Warning: {program}: the YYYYMMDD argument is deprecated and ignored; "
            "artifacts are written to canonical dist paths.",
            file=sys.stderr,
        )
        return
    raise SystemExit(f"Usage: {program} [YYYYMMDD]")
