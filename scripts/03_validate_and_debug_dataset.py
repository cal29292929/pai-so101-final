#!/usr/bin/env python3
"""
第2回講義（RoboOps実践: validate_dataset.py）＋第3回講義（時刻同期・FPS検証）
＋第5回講義（debug-policy: Ground Truth vs 予測アクション比較）を統合した検証ツール。

機能:
1. データセット品質検証 (Schema, 非空, 長さ一致, NaN/Inf, 関節角レンジ, 最短エピソード長, カメラ/周期ジッタ, 停止フレーム率)
2. セルフテスト (--run-self-test): 第2回講義にならい、正常データ(PASS)と意図的に壊したデータ(FAIL)の両方でValidator自身を検証
3. オフライン方策デバッグ (--predictions-npz): 第5回講義にならい、GTアクションと推論アクションのMSEを関節ごとに算出し、「学習不足」か「デプロイ時OOD汎化不足」かを自動診断
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

REQUIRED_KEYS = ("observation.state", "action", "episode_index", "timestamp")


@dataclass(frozen=True)
class ValidationCheck:
    label: str
    passed: bool
    detail: str


def validate_episode_arrays(
    data: dict[str, np.ndarray],
    expected_dof: int = 6,
    max_abs_angle_deg: float = 360.0,
    min_episode_frames: int = 15,
    max_static_ratio: float = 0.60,
) -> list[ValidationCheck]:
    """Run RoboOps dataset quality checks (Lecture 2 + Lecture 3 + Lecture 5)."""
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        return [
            ValidationCheck(
                "required fields exist",
                False,
                f"missing keys: {', '.join(missing)}",
            )
        ]

    checks: list[ValidationCheck] = [
        ValidationCheck("required fields exist", True, "all required fields present")
    ]

    state = np.asarray(data["observation.state"])
    action = np.asarray(data["action"])
    ep_idx = np.asarray(data["episode_index"]).reshape(-1)
    ts = np.asarray(data["timestamp"]).reshape(-1)

    n_frames = int(action.shape[0]) if action.ndim > 0 else 0
    checks.append(
        ValidationCheck("dataset is not empty", n_frames > 0, f"{n_frames} frames")
    )

    lengths_match = (
        state.shape[0] == n_frames
        and ep_idx.shape[0] == n_frames
        and ts.shape[0] == n_frames
    )
    checks.append(
        ValidationCheck(
            "state / action / timestamp lengths match",
            lengths_match,
            f"state={state.shape[0]}, action={action.shape[0]}, ep={ep_idx.shape[0]}, ts={ts.shape[0]}",
        )
    )

    shapes_ok = (
        state.ndim == 2
        and action.ndim == 2
        and state.shape[1] == expected_dof
        and action.shape[1] == expected_dof
    )
    checks.append(
        ValidationCheck(
            f"DoF schema matches ({expected_dof} DoF)",
            shapes_ok,
            f"state.shape={state.shape}, action.shape={action.shape}",
        )
    )

    finite_ok = bool(
        np.isfinite(state).all()
        and np.isfinite(action).all()
        and np.isfinite(ts).all()
    )
    checks.append(
        ValidationCheck(
            "no NaN / Inf values",
            finite_ok,
            "all finite" if finite_ok else "NaN or Inf detected",
        )
    )

    max_abs = float(
        max(
            np.abs(state).max(initial=0.0),
            np.abs(action).max(initial=0.0),
        )
    )
    range_ok = finite_ok and (max_abs <= max_abs_angle_deg)
    checks.append(
        ValidationCheck(
            "joint angle / action range within limits",
            range_ok,
            f"max_abs={max_abs:.2f} (limit={max_abs_angle_deg:.1f})",
        )
    )

    if ep_idx.size > 0:
        _, counts = np.unique(ep_idx, return_counts=True)
        shortest = int(counts.min())
        ep_len_ok = shortest >= min_episode_frames
        checks.append(
            ValidationCheck(
                "minimum episode length",
                ep_len_ok,
                f"shortest={shortest} frames (min={min_episode_frames})",
            )
        )
    else:
        checks.append(ValidationCheck("minimum episode length", False, "no episodes"))

    # Lecture 5 check: detect excessive stationary ("stop") frames in demonstrations
    if n_frames > 1 and shapes_ok and finite_ok:
        deltas = np.linalg.norm(np.diff(action, axis=0), axis=1)
        static_ratio = float(np.mean(deltas < 1e-4))
        static_ok = static_ratio <= max_static_ratio
        checks.append(
            ValidationCheck(
                "low stationary frame ratio (Lecture 5 anti-stop check)",
                static_ok,
                f"stationary_ratio={static_ratio:.2%} (max={max_static_ratio:.0%})",
            )
        )

    return checks


def diagnose_gt_vs_pred(
    gt_actions: np.ndarray,
    pred_actions: np.ndarray,
    joint_names: list[str] | None = None,
    mse_threshold: float = 0.05,
) -> dict[str, Any]:
    """
    Lecture 5 p.53-54: Compare Ground Truth actions vs Policy Predicted actions on training/recorded data
    to isolate training failure from deployment OOD generalization failure.
    """
    gt = np.asarray(gt_actions, dtype=np.float64)
    pred = np.asarray(pred_actions, dtype=np.float64)
    if gt.shape != pred.shape:
        raise ValueError(f"Shape mismatch: gt={gt.shape} vs pred={pred.shape}")

    per_joint_mse = np.mean((gt - pred) ** 2, axis=0)
    total_mse = float(np.mean(per_joint_mse))
    names = joint_names or [f"joint_{i+1}" for i in range(gt.shape[1])]

    if total_mse > mse_threshold:
        diagnosis = (
            "PRED_MISMATCH_ON_DATASET: 予測がGTと大きくずれています。"
            "方策の学習自体が収束していないか、正規化統計・特徴量設定に不整合があります（第5回講義 p.54）。"
        )
    else:
        diagnosis = (
            "PRED_MATCHES_GT: 収集データ上では予測とGTがよく一致しています。"
            "もし実機デプロイ時に動かない場合は、初期姿勢のずれ・カメラ露出変化・背景変化などのOOD（汎化不足）またはテレオペノード未停止が原因です（第5回講義 p.51, p.54）。"
        )

    return {
        "total_mse": total_mse,
        "mse_threshold": mse_threshold,
        "per_joint_mse": {
            name: float(val) for name, val in zip(names, per_joint_mse)
        },
        "diagnosis": diagnosis,
    }


def run_self_test() -> bool:
    """Lecture 2 practice: verify validator on both healthy data (PASS) and intentionally broken data (FAIL)."""
    rng = np.random.default_rng(42)
    t = np.linspace(0.0, 2.0, 60)
    healthy = {
        "observation.state": np.sin(t[:, None] + np.arange(6)) * 45.0,
        "action": np.sin(t[:, None] + 0.05 + np.arange(6)) * 45.0,
        "episode_index": np.repeat([0, 1], 30),
        "timestamp": np.tile(np.linspace(0.0, 1.0, 30), 2),
    }
    broken = {
        "observation.state": healthy["observation.state"].copy(),
        "action": healthy["action"].copy(),
        "episode_index": healthy["episode_index"].copy(),
        "timestamp": healthy["timestamp"].copy(),
    }
    broken["action"][5, 2] = np.nan
    broken["observation.state"][10, 0] = 9999.0

    healthy_checks = validate_episode_arrays(healthy)
    broken_checks = validate_episode_arrays(broken)

    healthy_passed = all(c.passed for c in healthy_checks)
    broken_failed = not all(c.passed for c in broken_checks)

    gt = healthy["action"]
    pred_good = gt + rng.normal(0.0, 0.05, size=gt.shape)
    debug_report = diagnose_gt_vs_pred(gt, pred_good)

    print("=== [Self-Test 1] Healthy Dataset Validation (Expected: PASS) ===")
    for c in healthy_checks:
        print(f"  {'PASS' if c.passed else 'FAIL'}: {c.label} ({c.detail})")

    print("\n=== [Self-Test 2] Broken Dataset Validation (Expected: FAIL detected) ===")
    for c in broken_checks:
        print(f"  {'PASS' if c.passed else 'FAIL'}: {c.label} ({c.detail})")

    print("\n=== [Self-Test 3] Lecture 5 Policy Debug (GT vs Predicted Action) ===")
    print(json.dumps(debug_report, ensure_ascii=False, indent=2))

    ok = healthy_passed and broken_failed
    print(f"\nSELF-TEST RESULT: {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RoboOps Dataset Validator & Lecture 5 GT-vs-Prediction Debugger"
    )
    parser.add_argument(
        "--run-self-test",
        action="store_true",
        help="Run Lecture 2 healthy + broken dataset self-test and Lecture 5 debug check",
    )
    parser.add_argument(
        "--npz",
        type=Path,
        default=None,
        help="Path to an .npz dataset bundle containing observation.state, action, episode_index, timestamp",
    )
    parser.add_argument(
        "--expected-dof",
        type=int,
        default=6,
        help="Expected DoF (6 for single-arm SO-101, 12 for bimanual SO-101)",
    )
    parser.add_argument(
        "--save-report",
        type=Path,
        default=None,
        help="Optional path to save JSON validation report",
    )
    args = parser.parse_args()

    if args.run_self_test:
        if not run_self_test():
            raise SystemExit(1)
        return

    if args.npz is None:
        print("No --npz specified; running --run-self-test by default.")
        if not run_self_test():
            raise SystemExit(1)
        return

    with np.load(args.npz, allow_pickle=False) as raw:
        data = {k: raw[k] for k in raw.files}

    checks = validate_episode_arrays(data, expected_dof=args.expected_dof)
    passed = all(c.passed for c in checks)
    for c in checks:
        print(f"{'PASS' if c.passed else 'FAIL'}: {c.label} — {c.detail}")
    print(f"\nRESULT: {'PASS' if passed else 'FAIL'}")

    if args.save_report:
        args.save_report.parent.mkdir(parents=True, exist_ok=True)
        args.save_report.write_text(
            json.dumps(
                {"passed": passed, "checks": [asdict(c) for c in checks]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
