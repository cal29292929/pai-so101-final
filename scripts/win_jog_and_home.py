#!/usr/bin/env python3
"""SO-101 Follower を低速で指定関節だけ動かし、現在姿勢をホームとして保存・復帰する (lerobot 0.6.1)。

安全方針:
- 指定した関節だけを動かし、他の関節は現在値で保持する。
- 速度は --speed（deg/s、既定 8）で線形補間。lerobot の max_relative_target も併用。
- 目標値は safe_rollout.py と同じ安全上限（設定可動域 × --limit-scale）にクリップする。
- 動かす前に「関節: 現在値 -> 目標値」を1行表示し、Enter で確認してから動かす（--yes で省略）。
- 終了時もトルクを保持する（disable_torque_on_disconnect=False）。持ち上げた腕が落ちないようにするため。

例（Windows, リポジトリ直下）:
  .venv\\Scripts\\python.exe scripts\\win_jog_and_home.py --show
  .venv\\Scripts\\python.exe scripts\\win_jog_and_home.py --move shoulder_lift=-40 elbow_flex=60
  .venv\\Scripts\\python.exe scripts\\win_jog_and_home.py --move shoulder_pan=15
  .venv\\Scripts\\python.exe scripts\\win_jog_and_home.py --save-home
  .venv\\Scripts\\python.exe scripts\\win_jog_and_home.py --goto-home
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs" / "so101_task_config.yaml"
HOME_FILE = ROOT / "configs" / "home_pose_catfood.yaml"
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


def _load_limits(scale: float) -> dict[str, tuple[float, float]]:
    spec = importlib.util.spec_from_file_location("safe_rollout", ROOT / "scripts" / "safe_rollout.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_limits(CFG, scale)


def plan_targets(current: dict[str, float], requested: dict[str, float],
                 limits: dict[str, tuple[float, float]]) -> dict[str, float]:
    """指定関節だけ目標値（安全上限でクリップ）にし、残りは現在値を保持した目標姿勢を返す。"""
    unknown = set(requested) - set(JOINTS)
    if unknown:
        raise ValueError(f"unknown joints: {sorted(unknown)}")
    target = dict(current)
    for j, v in requested.items():
        lo, hi = limits[j]
        target[j] = min(max(float(v), lo), hi)
    return target


def interpolate(start: dict[str, float], goal: dict[str, float], speed_deg_s: float, hz: float):
    """最大変化量の関節が speed_deg_s になるよう、start→goal の中間姿勢を順に返す。"""
    span = max(abs(goal[j] - start[j]) for j in start)
    n = max(1, int(span / speed_deg_s * hz) + 1)
    for i in range(1, n + 1):
        a = i / n
        yield {j: start[j] + (goal[j] - start[j]) * a for j in start}


def _parse_moves(items: list[str]) -> dict[str, float]:
    out = {}
    for it in items:
        k, _, v = it.partition("=")
        out[k.strip()] = float(v)
    return out


def _connect(port: str, robot_id: str):
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    cfg = SO101FollowerConfig(port=port, id=robot_id, max_relative_target=5.0,
                              disable_torque_on_disconnect=False)
    robot = SO101Follower(cfg)
    robot.connect(calibrate=False)
    return robot


def _read(robot) -> dict[str, float]:
    pos = robot.bus.sync_read("Present_Position")
    return {j: float(pos[j]) for j in JOINTS}


def _fmt(cur: dict[str, float], tgt: dict[str, float]) -> str:
    moved = [j for j in JOINTS if abs(tgt[j] - cur[j]) > 0.05]
    return ", ".join(f"{j}: {cur[j]:.1f} -> {tgt[j]:.1f}" for j in moved) or "(no change)"


def main() -> None:
    hw = yaml.safe_load(CFG.read_text(encoding="utf-8"))["hardware"]["arms"]["follower_1"]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--show", action="store_true", help="現在の関節角を表示するだけ")
    g.add_argument("--move", nargs="+", metavar="JOINT=DEG", help="指定関節だけを目標値へ動かす")
    g.add_argument("--save-home", action="store_true", help=f"現在姿勢を {HOME_FILE.name} に保存")
    g.add_argument("--goto-home", action="store_true", help="保存したホーム姿勢へ戻る")
    ap.add_argument("--speed", type=float, default=8.0, help="最大関節速度 deg/s（既定 8）")
    ap.add_argument("--hz", type=float, default=20.0)
    ap.add_argument("--limit-scale", type=float, default=0.8)
    ap.add_argument("--port", default=hw["port"])
    ap.add_argument("--id", default=hw["calibration_id"])
    ap.add_argument("--yes", action="store_true", help="移動前の確認を省略")
    args = ap.parse_args()

    robot = _connect(args.port, args.id)
    try:
        cur = _read(robot)
        if args.show:
            print("current: " + ", ".join(f"{j}={cur[j]:.1f}" for j in JOINTS))
            return
        if args.save_home:
            HOME_FILE.write_text(yaml.safe_dump({"home_deg": {j: round(cur[j], 1) for j in JOINTS}},
                                                sort_keys=False), encoding="utf-8")
            print(f"saved home to {HOME_FILE.relative_to(ROOT)}: " + ", ".join(f"{j}={cur[j]:.1f}" for j in JOINTS))
            return
        if args.goto_home:
            if not HOME_FILE.exists():
                sys.exit(f"{HOME_FILE.relative_to(ROOT)} not found: run --save-home first")
            requested = yaml.safe_load(HOME_FILE.read_text(encoding="utf-8"))["home_deg"]
        else:
            requested = _parse_moves(args.move)
        target = plan_targets(cur, requested, _load_limits(args.limit_scale))
        print(f"plan ({args.speed:.0f} deg/s): {_fmt(cur, target)}")
        if not args.yes and input("Enter で実行 / それ以外で中止: ").strip():
            print("aborted")
            return
        period = 1.0 / args.hz
        for step in interpolate(cur, target, args.speed, args.hz):
            t0 = time.perf_counter()
            robot.send_action({f"{j}.pos": v for j, v in step.items()})
            time.sleep(max(0.0, period - (time.perf_counter() - t0)))
        time.sleep(0.5)
        print("reached: " + ", ".join(f"{j}={v:.1f}" for j, v in _read(robot).items()))
    finally:
        robot.disconnect()  # torque stays enabled (disable_torque_on_disconnect=False)


if __name__ == "__main__":
    main()
