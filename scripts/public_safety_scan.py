"""Scan public project files for terms that should be reviewed before publishing."""

from __future__ import annotations

import re
from pathlib import Path

from ev_flex_trading.config import PROJECT_ROOT

REVIEW_PATTERNS = [
    r"\bMasdar\b",
    r"\bZenobe\s+data\b",
    r"\bconfidential\b",
    r"\bcolleague\b",
    r"\blender\b",
    r"\btransaction\b",
    r"\binternal workstream\b",
    r"\bguaranteed trading\b",
    r"\bproduction trading system\b",
    r"\bfinancial advice\b",
    r"API_KEY",
    r"\bpassword\b",
    r"\bsecret\b",
    r"\btoken\b",
    r"C:\\Users\\",
    r"C:/Users/",
    r"[\w.+-]+@[\w-]+\.[\w.-]+",
]

INCLUDED_SUFFIXES = {
    ".css",
    ".csv",
    ".example",
    ".html",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
}
SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "__pycache__",
    "ev_flex_trading_ops.egg-info",
    "node_modules",
    "dist",
}
SKIP_FILES = {"public_safety_scan.py"}

ACCEPTABLE_CONTEXT = [
    "Do not commit secrets",
    "no secrets",
    "private_notes",
    "not a production trading system",
    "production trading, dispatch, or official settlement system",
    "financial advice",
    "api_key|secret|token|password",
    "Do not include private job-search strategy",
    "guaranteed trading profits",
    "production trading system claims",
    "- production trading system",
    "colleague, lender, transaction",
]


def _is_candidate(path: Path) -> bool:
    if any(part in SKIP_PARTS for part in path.parts):
        return False
    if path.name in SKIP_FILES:
        return False
    return path.suffix in INCLUDED_SUFFIXES or path.name == ".gitignore"


def _is_acceptable(line: str) -> bool:
    lowered = line.lower()
    return any(context.lower() in lowered for context in ACCEPTABLE_CONTEXT)


def main() -> int:
    findings: list[tuple[Path, int, str]] = []
    combined = re.compile("|".join(f"({pattern})" for pattern in REVIEW_PATTERNS), re.I)

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or not _is_candidate(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if combined.search(line) and not _is_acceptable(line):
                findings.append((path.relative_to(PROJECT_ROOT), line_number, line.strip()))

    if findings:
        print("Public-safety scan found review items:")
        for path, line_number, line in findings:
            print(f"{path}:{line_number}: {line}")
        return 1

    print("Public-safety scan passed: no review items found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
