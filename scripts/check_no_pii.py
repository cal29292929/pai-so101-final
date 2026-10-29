#!/usr/bin/env python3
"""
提出前・GitHub Push前の個人情報・禁止ワード自動検査スクリプト。
レポート原稿、作業ログ(WORK_LOG.md)、README、スクリプト、設定ファイル、および git コミット履歴内に
個人情報パターンが含まれていないかを検査します。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Patterns that must never appear in public deliverables
FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("Japanese phone number", re.compile(r"\b0\d{1,4}-\d{1,4}-\d{4}\b")),
    ("Local macOS/Linux username path", re.compile(r"/(Users|home)/(?!box\b|ubuntu\b|user\b)[A-Za-z0-9_.-]+/")),
    ("Sensitive welfare/facility/qualification terms", re.compile(r"(就労移行|支援施設|障害者手帳|受給者証)")),
]

ALLOWLIST_EMAILS = {
    "noreply@github.com",
    "cal29292929@users.noreply.github.com",
}


def scan_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return findings

    for line_no, line in enumerate(text.splitlines(), 1):
        for label, pat in FORBIDDEN_PATTERNS:
            if path.name == "check_no_pii.py" and label == "Sensitive welfare/facility/qualification terms":
                continue
            for m in pat.finditer(line):
                matched = m.group(0)
                if label == "Email address" and matched in ALLOWLIST_EMAILS:
                    continue
                findings.append(f"{path.relative_to(ROOT)}:{line_no} [{label}] -> {matched}")
    return findings


def check_git_metadata() -> list[str]:
    findings: list[str] = []
    if not (ROOT / ".git").exists():
        return findings
    try:
        res = subprocess.run(
            ["git", "log", "--format=%H %an <%ae>"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.splitlines():
                for label, pat in FORBIDDEN_PATTERNS:
                    for m in pat.finditer(line):
                        matched = m.group(0)
                        if label == "Email address" and matched in ALLOWLIST_EMAILS:
                            continue
                        findings.append(f"git-log [{label}] -> {line}")
    except Exception:
        pass
    return findings


def main() -> None:
    all_findings: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", "__pycache__", ".pytest_cache", "outputs", "data"} for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".mp4", ".pdf", ".npz", ".pt", ".safetensors"}:
            continue
        all_findings.extend(scan_file(path))

    all_findings.extend(check_git_metadata())

    if all_findings:
        print("FAIL: Potential PII or restricted terms detected:")
        for item in all_findings:
            print("  -", item)
        sys.exit(1)

    print("RESULT: PASS (Zero PII / restricted patterns found across repository files)")


if __name__ == "__main__":
    main()
