"""
Cat-food transfer task (blue bowl -> red bowl) pipeline contract tests.
=====================================================================
Windows 実機用スクリプト (scripts/win_*.ps1 / win_build_*.py) が
configs/so101_task_config.yaml と整合し、安全規約（CLAUDE.md §5）を守っているかを検証する。
実機・lerobot・Windows フォントが無い CI 環境でも実行できるよう、静的検査のみ行う。
"""
import py_compile
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ROBOT_PS1 = ["win_record_catfood.ps1", "win_eval_catfood.ps1"]
ALL_PS1 = ROBOT_PS1 + ["win_train_catfood.ps1"]
TASK_TEXT = "Scoop cat food from the blue bowl and drop it into the red bowl."


def _cfg():
    return yaml.safe_load((ROOT / "configs" / "so101_task_config.yaml").read_text(encoding="utf-8"))


def _read(name: str) -> str:
    return (SCRIPTS / name).read_text(encoding="utf-8")


def _param_default(text: str, value: str) -> str:
    """値が PowerShell 変数 ($Name) なら param() の既定値を返す。"""
    if not value.startswith("$"):
        return value
    d = re.search(r"\[(?:int|double)\]%s\s*=\s*([\d.]+)" % re.escape(value), text)
    assert d, f"no default for {value}"
    return d.group(1)


def test_catfood_scripts_present_and_compile():
    for name in ALL_PS1 + ["win_build_report.py", "win_build_video.py"]:
        assert (SCRIPTS / name).exists(), f"{name} missing"
    for name in ["win_build_report.py", "win_build_video.py"]:
        py_compile.compile(str(SCRIPTS / name), doraise=True)


def test_robot_scripts_respect_max_delta():
    """Follower への目標角変化は max_delta_deg (15°) 以下に制限されていること。"""
    limit = float(_cfg().get("safety", {}).get("max_delta_deg_per_step", 15.0))
    for name in ROBOT_PS1:
        text = _read(name)
        m = re.search(r"--robot\.max_relative_target=(\$?[\w.]+)", text)
        assert m, f"{name}: --robot.max_relative_target is not set"
        val = _param_default(text, m.group(1))
        assert float(val) <= limit, f"{name}: max_relative_target {val} > {limit}"


def test_robot_scripts_match_hardware_config():
    hw = _cfg()["hardware"]
    follower = hw["arms"]["follower_1"]
    leader = hw["arms"]["leader_1"]
    wrist_idx = hw["cameras"]["wrist_cam"]["index_or_path"]
    for name in ROBOT_PS1:
        text = _read(name)
        assert f"--robot.port={follower['port']}" in text, f"{name}: follower port mismatch"
        assert f"--robot.id={follower['calibration_id']}" in text, f"{name}: follower calibration id mismatch"
        m = re.search(r"index_or_path: (\$?\w+)", text)
        assert m, f"{name}: wrist camera index not set"
        idx = _param_default(text, m.group(1))
        assert idx == str(wrist_idx), f"{name}: wrist camera index {idx} != config {wrist_idx}"
    rec = _read("win_record_catfood.ps1")
    assert f"--teleop.port={leader['port']}" in rec
    assert f"--teleop.id={leader['calibration_id']}" in rec


def test_task_text_consistent_and_no_hub_upload():
    """学習データと評価で同じタスク文を使い、データ/モデルを Hub へ送らないこと。"""
    for name in ROBOT_PS1:
        text = _read(name)
        assert TASK_TEXT in text, f"{name}: task text differs from training data"
        assert "--dataset.push_to_hub=false" in text
    train = _read("win_train_catfood.ps1")
    assert "--policy.push_to_hub=false" in train
    assert "--wandb.enable=false" in train


def test_submission_pdf_name_rule():
    pdf = ROOT / "outputs" / "説明資料_PAI最終課題_cal29292929.pdf"
    assert pdf.exists(), "submission PDF (naming rule) missing"
    assert pdf.read_bytes()[:5] == b"%PDF-"


def _safe_rollout():
    import importlib.util
    spec = importlib.util.spec_from_file_location("safe_rollout", SCRIPTS / "safe_rollout.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_safe_rollout_limits_are_narrower_than_config():
    mod = _safe_rollout()
    cfg = _cfg()["safety"]["joint_limits_deg"]
    limits = mod.load_limits(ROOT / "configs" / "so101_task_config.yaml", 0.8)
    for joint, (lo, hi) in limits.items():
        assert cfg[joint][0] <= lo < hi <= cfg[joint][1], joint
    assert limits["wrist_roll"][0] >= -120.0 and limits["wrist_roll"][1] <= 120.0
    assert limits["gripper"] == (0.0, 100.0)


def test_safe_rollout_clamps_only_out_of_range_joints():
    import collections
    mod = _safe_rollout()
    limits = {"shoulder_lift": (-68.0, 68.0), "gripper": (0.0, 100.0)}
    counter = collections.Counter()
    out = mod.clamp_action({"shoulder_lift.pos": 90.0, "gripper.pos": 50.0, "other": 1}, limits, counter)
    assert out == {"shoulder_lift.pos": 68.0, "gripper.pos": 50.0, "other": 1}
    assert counter == {"shoulder_lift": 1}


def test_eval_runs_through_safe_rollout():
    text = _read("win_eval_catfood.ps1")
    assert "safe_rollout.py" in text
    assert "lerobot.scripts.lerobot_rollout" not in text


def _jog():
    import importlib.util
    spec = importlib.util.spec_from_file_location("jog", SCRIPTS / "win_jog_and_home.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_jog_moves_only_requested_joints_within_limits():
    mod = _jog()
    limits = mod._load_limits(0.8)
    cur = {j: 10.0 for j in mod.JOINTS}
    tgt = mod.plan_targets(cur, {"shoulder_lift": -200.0, "elbow_flex": 30.0}, limits)
    assert tgt["shoulder_lift"] == limits["shoulder_lift"][0]
    assert tgt["elbow_flex"] == 30.0
    for j in ["shoulder_pan", "wrist_flex", "wrist_roll", "gripper"]:
        assert tgt[j] == 10.0


def test_jog_interpolation_respects_speed():
    mod = _jog()
    start = {"a": 0.0, "b": 0.0}
    goal = {"a": 40.0, "b": -10.0}
    steps = list(mod.interpolate(start, goal, speed_deg_s=8.0, hz=20.0))
    assert steps[-1] == goal
    prev = start
    for s in steps:
        assert abs(s["a"] - prev["a"]) <= 8.0 / 20.0 + 1e-9
        prev = s
