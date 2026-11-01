#!/usr/bin/env python3
"""lerobot-rollout を安全機構付きで実行するラッパー (lerobot 0.6.1 / SO-101 Follower)。

ポリシー出力 → [EMA 平滑化] → [高さ下限(フロア)] → [関節角の安全上限] → lerobot の max_relative_target → サーボ

1. ホーム復帰（開始時・各リセット時・終了時）: configs/home_pose_catfood.yaml の姿勢へ、
   まず shoulder_lift / elbow_flex だけで持ち上げ（他の関節は保持）、その後 shoulder_pan など残りを動かす。
   lerobot の「起動時の姿勢へ戻る」処理をこの2段階移動に置き換える。
2. 平滑化: ポリシー出力に指数移動平均 (--ema-alpha, 1.0 で無効) をかけ、ぎくしゃくした動きを抑える。
3. 高さ下限: configs/floor_pose_catfood.yaml（皿の底すれすれの姿勢）があれば、shoulder_lift / elbow_flex が
   その値より「下がる側」へ行かないようにクリップする。下がる向きはホーム→フロアの差の符号で決める。
   関節ごとの近似であり、手先の高さを順運動学で計算しているわけではない。
4. 停止検知: エピソード中に全関節の変化が --stall-deg 未満のまま --stall-s 秒続いたら、
   そのエピソードを打ち切る（→ リセット時のホーム復帰が走る）。
5. 関節角の安全上限: safety.joint_limits_deg × --limit-scale にクリップ（gripper は対象外）。

使い方（下記以外の引数は lerobot-rollout にそのまま渡す）:
  python scripts/safe_rollout.py --limit-scale 0.8 --ema-alpha 0.3 --stall-s 4 \\
      --strategy.type=episodic --robot.type=so101_follower ... --robot.max_relative_target=5
"""
from __future__ import annotations

import argparse
import atexit
import collections
import logging
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CFG = ROOT / "configs" / "so101_task_config.yaml"
HOME_FILE = ROOT / "configs" / "home_pose_catfood.yaml"
FLOOR_FILE = ROOT / "configs" / "floor_pose_catfood.yaml"
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
LIFT_JOINTS = ("shoulder_lift", "elbow_flex")
log = logging.getLogger("safe_rollout")


# ---------------------------------------------------------------- pure helpers (tested)
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


def load_pose(path: Path, key: str) -> dict[str, float] | None:
    if not path.exists():
        return None
    return {j: float(v) for j, v in yaml.safe_load(path.read_text(encoding="utf-8"))[key].items()}


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


def floor_bounds(home: dict[str, float], floor: dict[str, float]) -> dict[str, tuple[float, int]]:
    """{joint: (フロア値, 下がる向き ±1)}。ホームとフロアがほぼ同じ関節は対象外。"""
    out = {}
    for j in LIFT_JOINTS:
        d = floor[j] - home[j]
        if abs(d) > 1.0:
            out[j] = (floor[j], 1 if d > 0 else -1)
    return out


def apply_floor(action: dict, bounds: dict[str, tuple[float, int]], counter=None) -> dict:
    out = dict(action)
    for j, (f, down) in bounds.items():
        key = f"{j}.pos"
        if key in out and (float(out[key]) - f) * down > 0:
            out[key] = f
            if counter is not None:
                counter[f"floor:{j}"] += 1
    return out


class EmaFilter:
    """"<joint>.pos" ごとの指数移動平均。alpha=1 で素通し。"""

    def __init__(self, alpha: float):
        if not 0.0 < alpha <= 1.0:
            raise ValueError(f"ema alpha must be in (0, 1], got {alpha}")
        self.alpha = alpha
        self.state: dict[str, float] = {}

    def reset(self, start: dict[str, float] | None = None) -> None:
        self.state = {f"{j}.pos": float(v) for j, v in (start or {}).items()}

    def __call__(self, action: dict) -> dict:
        out = dict(action)
        for key, val in action.items():
            if not key.endswith(".pos"):
                continue
            prev = self.state.get(key)
            s = float(val) if prev is None else self.alpha * float(val) + (1.0 - self.alpha) * prev
            self.state[key] = s
            out[key] = s
        return out


class StallDetector:
    """全関節の変化が tol_deg 未満のまま window_s 秒続いたら True。"""

    def __init__(self, window_s: float, tol_deg: float):
        self.window_s, self.tol = window_s, tol_deg
        self.reset()

    def reset(self) -> None:
        self.ref: dict[str, float] | None = None
        self.t_ref = 0.0

    def update(self, pos: dict[str, float], now: float) -> bool:
        if self.ref is None or any(abs(pos[j] - self.ref[j]) > self.tol for j in self.ref):
            self.ref, self.t_ref = dict(pos), now
            return False
        return now - self.t_ref >= self.window_s


def home_phases(current: dict[str, float], home: dict[str, float]) -> list[dict[str, float]]:
    """ホームへの2段階の目標姿勢: ①lift/elbow だけホーム値へ（他は保持） ②残りの関節もホーム値へ。"""
    p1 = dict(current)
    for j in LIFT_JOINTS:
        p1[j] = home[j]
    p2 = dict(p1)
    for j in JOINTS:
        if j in home:
            p2[j] = home[j]
    return [p1, p2]


def interpolate(start: dict[str, float], goal: dict[str, float], speed_deg_s: float, hz: float):
    """最大変化量の関節が speed_deg_s になるよう、start→goal の中間姿勢を順に返す。"""
    span = max(abs(goal[j] - start[j]) for j in start)
    n = max(1, int(span / speed_deg_s * hz) + 1)
    for i in range(1, n + 1):
        a = i / n
        yield {j: start[j] + (goal[j] - start[j]) * a for j in start}


def move_via(send, read, targets: list[dict[str, float]], speed_deg_s: float, hz: float = 20.0) -> None:
    """send({joint.pos}) / read()->{joint: deg} を使い、targets を順に低速でたどる。"""
    period = 1.0 / hz
    for tgt in targets:
        cur = read()
        tgt = {j: tgt.get(j, cur[j]) for j in cur}
        for step in interpolate(cur, tgt, speed_deg_s, hz):
            t0 = time.perf_counter()
            send({f"{j}.pos": v for j, v in step.items()})
            time.sleep(max(0.0, period - (time.perf_counter() - t0)))
    time.sleep(0.3)


# ---------------------------------------------------------------- lerobot patching
class Safety:
    def __init__(self, args):
        self.limits = load_limits(args.safety_config, args.limit_scale)
        self.home = load_pose(HOME_FILE, "home_deg")
        floor = load_pose(FLOOR_FILE, "floor_deg")
        self.floor = floor_bounds(self.home, floor) if (self.home and floor) else {}
        self.ema = EmaFilter(args.ema_alpha)
        self.stall = StallDetector(args.stall_s, args.stall_deg)
        self.home_speed = args.home_speed
        self.counter: collections.Counter = collections.Counter()
        self.policy_active = False  # True only inside the policy loop of an episode
        self.events: dict | None = None

    def filter_policy_action(self, action: dict) -> dict:
        a = self.ema(action)
        a = apply_floor(a, self.floor, self.counter)
        return clamp_action(a, self.limits, self.counter)

    def go_home(self, robot_wrapper) -> None:
        if not self.home:
            log.warning("[safe_rollout] %s not found: skip home move", HOME_FILE.name)
            return

        def read():
            obs = robot_wrapper.get_observation()
            return {j: float(obs[f"{j}.pos"]) for j in JOINTS}

        targets = [clamp_action({f"{j}.pos": v for j, v in p.items()}, self.limits) for p in
                   home_phases(read(), self.home)]
        targets = [{k.removesuffix(".pos"): v for k, v in t.items()} for t in targets]
        log.info("[safe_rollout] home: lift %s -> %s, then pan/wrist/gripper",
                 LIFT_JOINTS, {j: self.home[j] for j in LIFT_JOINTS})
        move_via(robot_wrapper.send_action, read, targets, self.home_speed)


def install(safety: Safety) -> None:
    from lerobot.robots.so_follower.so_follower import SOFollower
    from lerobot.rollout.strategies.core import RolloutStrategy
    from lerobot.rollout.strategies.episodic import EpisodicStrategy

    original_send = SOFollower.send_action

    def safe_send_action(self, action):
        if not safety.policy_active:  # home moves etc.: safety limits only
            return original_send(self, clamp_action(action, safety.limits, safety.counter))
        pos = self.bus.sync_read("Present_Position")
        pos = {j: float(pos[j]) for j in JOINTS}
        if not safety.ema.state:
            safety.ema.reset(pos)  # start smoothing from the current pose (no jump)
        if safety.stall.update(pos, time.perf_counter()) and safety.events is not None \
                and not safety.events.get("exit_early"):
            log.warning("[safe_rollout] joints still for %.1fs: ending episode early", safety.stall.window_s)
            safety.counter["stall_abort"] += 1
            safety.events["exit_early"] = True
        return original_send(self, safety.filter_policy_action(action))

    SOFollower.send_action = safe_send_action

    # Reset / teardown: replace "return to startup pose" with lift-then-home.
    def return_home(hw, duration_s: float = 3.0, fps: int = 50) -> None:
        safety.policy_active = False
        safety.go_home(hw.robot_wrapper)

    RolloutStrategy._return_to_initial_position = staticmethod(return_home)

    original_setup = EpisodicStrategy.setup
    original_policy_loop = EpisodicStrategy._policy_loop

    def setup(self, ctx):
        original_setup(self, ctx)
        safety.events = self._events
        safety.go_home(ctx.hardware.robot_wrapper)  # start from the home pose

    def policy_loop(self, *a, **kw):
        safety.ema.reset()
        safety.stall.reset()
        safety.policy_active = True
        try:
            return original_policy_loop(self, *a, **kw)
        finally:
            safety.policy_active = False

    EpisodicStrategy.setup = setup
    EpisodicStrategy._policy_loop = policy_loop


def main() -> None:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--safety-config", type=Path, default=DEFAULT_CFG)
    ap.add_argument("--limit-scale", type=float, default=0.8)
    ap.add_argument("--ema-alpha", type=float, default=0.3)
    ap.add_argument("--stall-s", type=float, default=4.0)
    ap.add_argument("--stall-deg", type=float, default=1.0)
    ap.add_argument("--home-speed", type=float, default=8.0, help="ホーム移動の最大関節速度 deg/s")
    ours, rest = ap.parse_known_args()

    safety = Safety(ours)
    print("[safe_rollout] joint limits (deg, gripper 0-100):")
    for j, (lo, hi) in safety.limits.items():
        print(f"  {j:14s} [{lo:7.1f}, {hi:7.1f}]")
    print(f"[safe_rollout] home={'yes' if safety.home else 'MISSING'} floor={safety.floor or 'none'} "
          f"ema_alpha={ours.ema_alpha} stall={ours.stall_s}s/<{ours.stall_deg}deg")
    install(safety)
    atexit.register(lambda: print(f"[safe_rollout] interventions: {dict(safety.counter) or 'none'}"))

    from lerobot.scripts import lerobot_rollout

    sys.argv = [sys.argv[0], *rest]
    lerobot_rollout.main()


if __name__ == "__main__":
    main()
