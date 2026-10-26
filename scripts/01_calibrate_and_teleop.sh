#!/usr/bin/env bash
# ==============================================================================
# SO-101 キャリブレーション＆テレオペレーション確認スクリプト
# Usage:
#   bash scripts/01_calibrate_and_teleop.sh single    # Step 1: 単腕構成
#   bash scripts/01_calibrate_and_teleop.sh bimanual  # Step 2: 双腕構成
# ==============================================================================
set -euo pipefail

MODE="${1:-single}"
LEADER_PORT="${LEADER_PORT:-/dev/ttyACM0}"
FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/ttyACM1}"
WRIST_CAM="${WRIST_CAM:-0}"
TOP_CAM="${TOP_CAM:-2}"

echo "=== Mode: ${MODE} ==="

if [ "${MODE}" = "single" ]; then
  echo "[Step 1] Single-Arm SO-101 Calibration & Teleop Commands:"
  cat << CMD_EOF

# 1. Port detection helper:
lerobot-find-port

# 2. Follower calibration:
lerobot-calibrate \\
  --robot.type=so101_follower \\
  --robot.port=${FOLLOWER_PORT} \\
  --robot.id=so101_follower_arm1

# 3. Leader calibration:
lerobot-calibrate \\
  --teleop.type=so101_leader \\
  --teleop.port=${LEADER_PORT} \\
  --teleop.id=so101_leader_arm1

# 4. Teleoperation with Wrist Camera + Overhead Camera:
lerobot-teleoperate \\
  --robot.type=so101_follower \\
  --robot.port=${FOLLOWER_PORT} \\
  --robot.id=so101_follower_arm1 \\
  --robot.cameras="{ wrist: {type: opencv, index_or_path: ${WRIST_CAM}, width: 640, height: 480, fps: 30}, top: {type: opencv, index_or_path: ${TOP_CAM}, width: 640, height: 480, fps: 30} }" \\
  --teleop.type=so101_leader \\
  --teleop.port=${LEADER_PORT} \\
  --teleop.id=so101_leader_arm1 \\
  --display_data=true
CMD_EOF

elif [ "${MODE}" = "bimanual" ]; then
  echo "[Step 2] Bimanual SO-101 (2x Leader + 2x Follower) Calibration & Teleop Commands:"
  cat << BI_EOF

# Bimanual Teleoperation (Left + Right SO-101 Arms + Cameras):
lerobot-teleoperate \\
  --robot.type=bi_so101_follower \\
  --robot.left_arm_port=/dev/ttySO101_follower_left \\
  --robot.right_arm_port=/dev/ttySO101_follower_right \\
  --robot.id=bi_so101_follower \\
  --robot.cameras="{ wrist_right: {type: opencv, index_or_path: ${WRIST_CAM}, width: 640, height: 480, fps: 30}, top: {type: opencv, index_or_path: ${TOP_CAM}, width: 640, height: 480, fps: 30} }" \\
  --teleop.type=bi_so101_leader \\
  --teleop.left_arm_port=/dev/ttySO101_leader_left \\
  --teleop.right_arm_port=/dev/ttySO101_leader_right \\
  --teleop.id=bi_so101_leader \\
  --display_data=true
BI_EOF
else
  echo "Unknown mode: ${MODE}. Use 'single' or 'bimanual'."
  exit 1
fi
