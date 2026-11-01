"""scripts/safe_rollout.py の安全機構テスト（lerobot をスタブに置き換えて実機なしで検証）。"""
import argparse
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


def _mod():
    spec = importlib.util.spec_from_file_location("safe_rollout_t", ROOT / "scripts" / "safe_rollout.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_home_phases_lift_first_then_pan():
    m = _mod()
    cur = {j: 0.0 for j in JOINTS}
    home = {"shoulder_pan": 30.0, "shoulder_lift": -40.0, "elbow_flex": 50.0,
            "wrist_flex": 10.0, "wrist_roll": 5.0, "gripper": 20.0}
    p1, p2 = m.home_phases(cur, home)
    assert p1 == {**cur, "shoulder_lift": -40.0, "elbow_flex": 50.0}  # pan unchanged while lifting
    assert p2 == home


def test_ema_smooths_from_start_pose():
    m = _mod()
    f = m.EmaFilter(0.25)
    f.reset({"shoulder_lift": 0.0})
    assert f({"shoulder_lift.pos": 40.0})["shoulder_lift.pos"] == 10.0
    assert f({"shoulder_lift.pos": 40.0})["shoulder_lift.pos"] == 17.5


def test_floor_blocks_only_downward_direction():
    m = _mod()
    home = {"shoulder_lift": -40.0, "elbow_flex": 60.0}
    floor = {"shoulder_lift": 20.0, "elbow_flex": 30.0}  # down = +lift, -elbow
    b = m.floor_bounds(home, floor)
    assert b == {"shoulder_lift": (20.0, 1), "elbow_flex": (30.0, -1)}
    out = m.apply_floor({"shoulder_lift.pos": 35.0, "elbow_flex.pos": 10.0}, b)
    assert out == {"shoulder_lift.pos": 20.0, "elbow_flex.pos": 30.0}
    ok = {"shoulder_lift.pos": 0.0, "elbow_flex.pos": 45.0}
    assert m.apply_floor(ok, b) == ok


def test_stall_detector():
    m = _mod()
    s = m.StallDetector(window_s=4.0, tol_deg=1.0)
    pos = {"a": 0.0}
    assert not s.update(pos, 0.0)
    assert not s.update({"a": 0.5}, 3.9)
    assert s.update({"a": 0.5}, 4.1)
    assert not s.update({"a": 2.0}, 4.2)  # moved: timer restarts


def _install_with_stubs(m, tmp_path, monkeypatch):
    sent = []

    class FakeBus:
        def __init__(self):
            self.pos = {j: 0.0 for j in JOINTS}

        def sync_read(self, _name):
            return dict(self.pos)

    class SOFollower:
        def __init__(self):
            self.bus = FakeBus()

        def send_action(self, action):
            sent.append(dict(action))
            for k, v in action.items():
                self.bus.pos[k.removesuffix(".pos")] = v
            return action

    class RolloutStrategy:
        pass

    class EpisodicStrategy(RolloutStrategy):
        def setup(self, ctx):
            self._events = {"exit_early": False}

        def _policy_loop(self, actions):
            for a in actions:
                if self._events["exit_early"]:
                    break
                ctx_robot.send_action(a)

    mods = {
        "lerobot": types.ModuleType("lerobot"),
        "lerobot.robots": types.ModuleType("lerobot.robots"),
        "lerobot.robots.so_follower": types.ModuleType("lerobot.robots.so_follower"),
        "lerobot.robots.so_follower.so_follower": types.SimpleNamespace(SOFollower=SOFollower),
        "lerobot.rollout": types.ModuleType("lerobot.rollout"),
        "lerobot.rollout.strategies": types.ModuleType("lerobot.rollout.strategies"),
        "lerobot.rollout.strategies.core": types.SimpleNamespace(RolloutStrategy=RolloutStrategy),
        "lerobot.rollout.strategies.episodic": types.SimpleNamespace(EpisodicStrategy=EpisodicStrategy),
    }
    for k, v in mods.items():
        monkeypatch.setitem(sys.modules, k, v)

    home = tmp_path / "home.yaml"
    home.write_text("home_deg: {shoulder_pan: 20.0, shoulder_lift: -30.0, elbow_flex: 40.0, "
                    "wrist_flex: 0.0, wrist_roll: 0.0, gripper: 10.0}\n", encoding="utf-8")
    floor = tmp_path / "floor.yaml"
    floor.write_text("floor_deg: {shoulder_pan: 0.0, shoulder_lift: 10.0, elbow_flex: 20.0, "
                     "wrist_flex: 0.0, wrist_roll: 0.0, gripper: 10.0}\n", encoding="utf-8")
    monkeypatch.setattr(m, "HOME_FILE", home)
    monkeypatch.setattr(m, "FLOOR_FILE", floor)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    args = argparse.Namespace(safety_config=ROOT / "configs" / "so101_task_config.yaml", limit_scale=0.8,
                              ema_alpha=0.5, stall_s=4.0, stall_deg=1.0, home_speed=1000.0)
    safety = m.Safety(args)
    m.install(safety)

    robot = SOFollower()
    ctx_robot = robot

    class Wrapper:
        def get_observation(self):
            return {f"{j}.pos": v for j, v in robot.bus.pos.items()}

        def send_action(self, a):
            return robot.send_action(a)

    hw = types.SimpleNamespace(robot_wrapper=Wrapper(), initial_position={"x": 1})
    ctx = types.SimpleNamespace(hardware=hw)
    return safety, robot, sent, EpisodicStrategy, RolloutStrategy, ctx, hw


def test_setup_lifts_before_pan_and_reaches_home(tmp_path, monkeypatch):
    m = _mod()
    safety, robot, sent, Ep, _, ctx, _ = _install_with_stubs(m, tmp_path, monkeypatch)
    Ep().setup(ctx)
    assert robot.bus.pos["shoulder_pan"] == 20.0 and robot.bus.pos["shoulder_lift"] == -30.0
    lift_done = next(i for i, a in enumerate(sent) if a["shoulder_lift.pos"] == -30.0)
    assert all(a["shoulder_pan.pos"] == 0.0 for a in sent[: lift_done + 1])  # no pan while lifting


def test_policy_actions_are_smoothed_floored_and_stall_aborts(tmp_path, monkeypatch):
    m = _mod()
    safety, robot, sent, Ep, _, ctx, _ = _install_with_stubs(m, tmp_path, monkeypatch)
    ep = Ep()
    ep.setup(ctx)
    sent.clear()
    clock = iter(range(0, 1000))
    monkeypatch.setattr(m.time, "perf_counter", lambda: float(next(clock)))
    deep = {**{f"{j}.pos": robot.bus.pos[j] for j in JOINTS}, "shoulder_lift.pos": 60.0}
    ep._policy_loop([deep] * 20)
    lifts = [a["shoulder_lift.pos"] for a in sent]
    assert lifts[0] < 60.0  # EMA: no jump to the target
    assert max(lifts) <= 10.0  # floor (down = +lift) is never crossed
    assert ep._events["exit_early"] is True  # stuck at the floor -> episode ended early
    assert safety.counter["stall_abort"] == 1


def test_reset_uses_home_not_startup_pose(tmp_path, monkeypatch):
    m = _mod()
    safety, robot, sent, Ep, RS, ctx, hw = _install_with_stubs(m, tmp_path, monkeypatch)
    robot.bus.pos.update({"shoulder_pan": -15.0, "shoulder_lift": 5.0})
    RS._return_to_initial_position(hw=hw, duration_s=1)
    assert robot.bus.pos["shoulder_pan"] == 20.0 and robot.bus.pos["shoulder_lift"] == -30.0
