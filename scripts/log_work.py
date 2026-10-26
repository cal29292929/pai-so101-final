#!/usr/bin/env python3
"""
作業報告・実験ログ記録スクリプト (`scripts/log_work.py`)
============================================================
最終課題の設計・実機テスト・データ収集・学習・Slack知見などを
`docs/WORK_LOG.md` にタイムスタンプ付きで自動追記し、
必要に応じて PII チェック (`check_no_pii.py`)、レポートPDF再生成 (`05_build_video_and_report.py`)、
および GitHub への commit / push を行います。

Usage Examples:
  python3 scripts/log_work.py \
    --category hardware-test \
    --title "SO-101 Unit 1 リストカメラ・サーボ接続確認" \
    --summary "Leader/Follower 各6軸と手首UVCカメラの認識・キャリブレーション完了" \
    --details "ttySO101_leader, ttySO101_follower_right を udev 固定。wrist_cam 640x480@30fps 確認。" \
    --metrics "fps=30.0, joints=6/6 OK" \
    --commit --push
"""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
WORK_LOG_PATH = ROOT / "docs" / "WORK_LOG.md"
MARKER_END = "<!-- WORK_LOG_ENTRIES_END -->"


def get_next_log_number(text: str) -> int:
    nums = [int(m.group(1)) for m in re.finditer(r"^### Log #(\d+):", text, flags=re.MULTILINE)]
    return (max(nums) + 1) if nums else 1


def format_entry(
    log_num: int,
    timestamp: str,
    category: str,
    title: str,
    summary: str,
    details: list[str],
    metrics: list[str],
) -> str:
    lines = [
        f"### Log #{log_num}: {title}",
        f"- **Timestamp**: `{timestamp}`",
        f"- **Category**: `{category}`",
        f"- **Summary**: {summary}",
    ]
    if details:
        lines.append("- **Details**:")
        for d in details:
            lines.append(f"  - {d}")
    if metrics:
        lines.append("- **Metrics / Artifacts**:")
        for m in metrics:
            lines.append(f"  - {m}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a structured work log entry to docs/WORK_LOG.md")
    parser.add_argument("--category", default="experiment", help="Category tag (e.g., hardware-test, dataset, training, eval, slack-info)")
    parser.add_argument("--title", required=True, help="Short title of the work log entry")
    parser.add_argument("--summary", required=True, help="One-sentence summary of what was done/found")
    parser.add_argument("--details", nargs="*", default=[], help="Detailed bullet points")
    parser.add_argument("--metrics", nargs="*", default=[], help="Quantitative metrics or artifact paths")
    parser.add_argument("--rebuild-report", action="store_true", help="Regenerate PDF report after logging")
    parser.add_argument("--commit", action="store_true", help="Run check_no_pii.py and git commit the updated WORK_LOG.md")
    parser.add_argument("--push", action="store_true", help="Push commit to origin main (implies --commit)")
    args = parser.parse_args()

    if not WORK_LOG_PATH.exists():
        print(f"ERROR: {WORK_LOG_PATH} does not exist.", file=sys.stderr)
        sys.exit(1)

    text = WORK_LOG_PATH.read_text(encoding="utf-8")
    log_num = get_next_log_number(text)
    now_jst = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")

    entry_md = format_entry(
        log_num=log_num,
        timestamp=now_jst,
        category=args.category,
        title=args.title,
        summary=args.summary,
        details=args.details,
        metrics=args.metrics,
    )

    if MARKER_END in text:
        updated = text.replace(MARKER_END, f"{entry_md}\n{MARKER_END}")
    else:
        updated = text.rstrip() + "\n\n" + entry_md + "\n"

    WORK_LOG_PATH.write_text(updated, encoding="utf-8")
    print(f"[OK] Appended Log #{log_num} ({args.title}) to {WORK_LOG_PATH.relative_to(ROOT)}")

    # Always run PII check after updating work log
    pii_check = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_no_pii.py")], cwd=ROOT)
    if pii_check.returncode != 0:
        print("[ERROR] PII check failed! Please remove any personal info from the log entry.", file=sys.stderr)
        sys.exit(1)

    if args.rebuild_report:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "05_build_video_and_report.py")], cwd=ROOT, check=True)

    if args.commit or args.push:
        subprocess.run(["git", "add", "docs/WORK_LOG.md"], cwd=ROOT, check=True)
        if args.rebuild_report:
            subprocess.run(["git", "add", "outputs/"], cwd=ROOT, check=False)
        msg = f"docs(work-log): add Log #{log_num} - {args.title}"
        subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
        print(f"[OK] Committed: {msg}")

    if args.push:
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
        print("[OK] Pushed to origin/main")


if __name__ == "__main__":
    main()
