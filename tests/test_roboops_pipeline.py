"""
RoboOps Automated Quality & Safety Verification Tests (Day 2 & Day 5 Standards)
==============================================================================
Verifies:
1. Joint limit & wrist camera cable anti-snag bounds (`wrist_roll` within [-120, +120])
2. Trajectory delta clamping (max step <= 15 deg per control tick) via `clamp_and_interpolate`
3. Active perception close-up IK vs grasp IK height separation
4. Dataset Validator self-test (valid dataset PASS, corrupted dataset FAIL)
5. Repository-wide Zero-PII scanner (`check_no_pii.py`)
6. Work Log (`docs/WORK_LOG.md`) & `scripts/log_work.py` structure
"""
import importlib.util
import subprocess
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_controller_module():
    spec = importlib.util.spec_from_file_location(
        "vlm_ctrl", ROOT / "scripts" / "03_vlm_zero_shot_controller.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vlm_ctrl"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_config_safety_and_privacy():
    cfg_path = ROOT / "configs" / "so101_task_config.yaml"
    assert cfg_path.exists(), "Config file missing"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    assert cfg["project"]["omnicampus_account_name"] == "cal29292929"
    assert cfg["project"]["omnicampus_account_id"] == "KfvZJ6"
    wrist_roll_limits = cfg["safety"]["joint_limits_deg"]["wrist_roll"]
    assert wrist_roll_limits[0] >= -120.0 and wrist_roll_limits[1] <= 120.0


def test_joint_clamping_and_interpolation():
    mod = load_controller_module()
    cfg = yaml.safe_load((ROOT / "configs" / "so101_task_config.yaml").read_text(encoding="utf-8"))
    limits = cfg["safety"]["joint_limits_deg"]

    current = {j: 0.0 for j in mod.JOINT_NAMES}
    extreme_target = {
        "shoulder_pan": 999.0,
        "shoulder_lift": -999.0,
        "elbow_flex": 500.0,
        "wrist_flex": -500.0,
        "wrist_roll": 180.0,
        "gripper": 200.0,
    }
    traj = mod.clamp_and_interpolate(current, extreme_target, limits, max_delta_deg=15.0, steps=20)
    assert len(traj) == 20
    prev = current
    for step in traj:
        for j in mod.JOINT_NAMES:
            lo, hi = limits[j]
            assert lo <= step[j] <= hi, f"Joint {j}={step[j]} out of bounds [{lo}, {hi}]"
            assert abs(step[j] - prev[j]) <= 15.0 + 1e-4, f"Step delta exceeded 15 deg on {j}"
        prev = step


def test_active_perception_ik_separation():
    mod = load_controller_module()
    closeup_pose = mod.pixel_to_so101_ik_pose(320, 240, close_up=True)
    grasp_pose = mod.pixel_to_so101_ik_pose(320, 240, close_up=False)
    # Close-up inspection pose keeps shoulder_lift higher (smaller angle) than grasp pose
    assert closeup_pose["shoulder_lift"] < grasp_pose["shoulder_lift"]


def test_dataset_validator_self_test():
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "03_validate_and_debug_dataset.py"), "--run-self-test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Validator self-test failed:\n{res.stdout}\n{res.stderr}"
    assert "SELF-TEST RESULT: PASS" in res.stdout


def test_no_pii_in_repository():
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_no_pii.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"PII check failed:\n{res.stdout}\n{res.stderr}"
    assert "RESULT: PASS" in res.stdout


def test_work_log_exists_and_populated():
    work_log = ROOT / "docs" / "WORK_LOG.md"
    assert work_log.exists(), "docs/WORK_LOG.md is missing"
    content = work_log.read_text(encoding="utf-8")
    assert "### Log #1:" in content
    assert "### Log #4:" in content
    assert "優秀生" in content
