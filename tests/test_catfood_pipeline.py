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


def test_catfood_scripts_present_and_compile():
    for name in ALL_PS1 + ["win_build_report.py", "win_build_video.py"]:
        assert (SCRIPTS / name).exists(), f"{name} missing"
    for name in ["win_build_report.py", "win_build_video.py"]:
        py_compile.compile(str(SCRIPTS / name), doraise=True)


def test_robot_scripts_respect_max_delta():
    """Follower への目標角変化は max_delta_deg (15°) 以下に制限されていること。"""
    limit = float(_cfg().get("safety", {}).get("max_delta_deg_per_step", 15.0))
    for name in ROBOT_PS1:
        m = re.search(r"--robot\.max_relative_target=(\d+(?:\.\d+)?)", _read(name))
        assert m, f"{name}: --robot.max_relative_target is not set"
        assert float(m.group(1)) <= limit, f"{name}: max_relative_target {m.group(1)} > {limit}"


def test_robot_scripts_match_hardware_config():
    hw = _cfg()["hardware"]
    follower = hw["arms"]["follower_1"]
    leader = hw["arms"]["leader_1"]
    wrist_idx = hw["cameras"]["wrist_cam"]["index_or_path"]
    for name in ROBOT_PS1:
        text = _read(name)
        assert f"--robot.port={follower['port']}" in text, f"{name}: follower port mismatch"
        assert f"--robot.id={follower['calibration_id']}" in text, f"{name}: follower calibration id mismatch"
        assert f"index_or_path: {wrist_idx}" in text, f"{name}: wrist camera index mismatch"
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
