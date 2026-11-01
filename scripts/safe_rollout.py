#!/usr/bin/env python3
"""lerobot-rollout を「関節角の安全上限」付きで実行するラッパー (lerobot 0.6.1 / SO-101)。

- SO-101 Follower への指令値を、configs/so101_task_config.yaml の safety.joint_limits_deg に
  --limit-scale を掛けた範囲へクリップしてから送る（垂れた配線が可動域の端で引っかかるのを防ぐ）。
  単位は lerobot 既定の use_degrees=True（各関節は度、gripper は 0-100）。
- クリップの後に lerobot 標準の --robot.max_relative_target（1ステップの最大変化量）が効くので、
  速度はそちらで落とす。
- クリップが起きた関節と回数を終了時に表示する。

使い方（--safety-config / --limit-scale 以外の引数は lerobot-rollout にそのまま渡す）:
  python scripts/safe_rollout.py --limit-scale 0.8 --robot.type=so101_follower ... --robot.max_relative_target=5
"""
from __future__ import annotations

import argparse
import atexit
import collections
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CFG = ROOT / "configs" / "so101_task_config.yaml"


def load_limits(cfg_path: Path, scale: float) -> dict[str, tuple[float, float]]:
    """設定の可動域を中心まわりに scale 倍へ狭める。gripper は開閉量なので狭めない。"""
    if not 0.0 < scale <= 1.0:
        raise ValueError(f"limit scale must be in (0, 1], got {scale}")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))["safety"]["joint_limits_deg"]
    limits = {}
    for joint, (lo, hi) in raw.items():
        lo, hi = float(lo), float(hi)
        if joint != "gripper":
            mid, half = (lo + hi) / 2.0, (hi - lo) / 2.0 * scale
            lo, hi = mid - half, mid + half
        limits[joint] = (lo, hi)
    return limits


def clamp_action(action: dict, limits: dict[str, tuple[float, float]], counter=None) -> dict:
    """"<joint>.pos" キーの値を limits に収める。その他のキーはそのまま返す。"""
    out = dict(action)
    for key, val in action.items():
        joint = key.removesuffix(".pos")
        if not key.endswith(".pos") or joint not in limits:
            continue
        lo, hi = limits[joint]
        v = float(val)
        c = min(max(v, lo), hi)
        if c != v:
            out[key] = c
            if counter is not None:
                counter[joint] += 1
    return out


def install(limits: dict[str, tuple[float, float]]) -> collections.Counter:
    from lerobot.robots.so_follower.so_follower import SOFollower

    counter: collections.Counter = collections.Counter()
    original = SOFollower.send_action

    def safe_send_action(self, action):
        return original(self, clamp_action(action, limits, counter))

    SOFollower.send_action = safe_send_action
    return counter


def main() -> None:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--safety-config", type=Path, default=DEFAULT_CFG)
    ap.add_argument("--limit-scale", type=float, default=0.8)
    ours, rest = ap.parse_known_args()

    limits = load_limits(ours.safety_config, ours.limit_scale)
    print("[safe_rollout] joint limits (deg, gripper 0-100):")
    for j, (lo, hi) in limits.items():
        print(f"  {j:14s} [{lo:7.1f}, {hi:7.1f}]")
    counter = install(limits)
    atexit.register(lambda: print(f"[safe_rollout] clamped commands per joint: {dict(counter) or 'none'}"))

    from lerobot.scripts import lerobot_rollout

    sys.argv = [sys.argv[0], *rest]
    lerobot_rollout.main()


if __name__ == "__main__":
    main()
