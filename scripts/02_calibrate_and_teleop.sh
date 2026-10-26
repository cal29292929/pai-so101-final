#!/usr/bin/env bash
# ==============================================================================
# 02_calibrate_and_teleop.sh
# SO-101 (Leader + Follower + Wrist Camera) のキャリブレーションとテレオペレーション実行
# 単腕 (Unit 1) および 双腕 (Unit 1 + Unit 2) の両方に対応
# ==============================================================================
set -euo pipefail

MODE="teleop"
FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/ttyACM0}"
LEADER_PORT="${LEADER_PORT:-/dev/ttyACM1}"
WRIST_CAM_INDEX="${WRIST_CAM_INDEX:-0}"
BIMANUAL="false"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --follower-port)
      FOLLOWER_PORT="$2"
      shift 2
      ;;
    --leader-port)
      LEADER_PORT="$2"
      shift 2
      ;;
    --wrist-cam)
      WRIST_CAM_INDEX="$2"
      shift 2
      ;;
    --bimanual)
      BIMANUAL="true"
      shift 1
      ;;
    --dry-run)
      DRY_RUN="true"
      shift 1
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--mode calibrate|teleop] [--follower-port /dev/ttyACM0] [--leader-port /dev/ttyACM1] [--wrist-cam 0] [--bimanual] [--dry-run]"
      exit 1
      ;;
  esac
done

echo "=================================================================="
echo " SO-101 Calibration & Teleoperation Launcher"
echo " Mode          : ${MODE}"
echo " Follower Port : ${FOLLOWER_PORT}"
echo " Leader Port   : ${LEADER_PORT}"
echo " Wrist Camera  : index ${WRIST_CAM_INDEX} (640x480 @ 30fps)"
echo " Bimanual Mode : ${BIMANUAL}"
echo "=================================================================="

run_cmd() {
  echo "+ $*"
  if [[ "${DRY_RUN}" == "false" ]]; then
    "$@"
  fi
}

if [[ "${MODE}" == "calibrate" ]]; then
  echo "[Step 1/2] Calibrating SO-101 Follower Arm (Unit 1)..."
  run_cmd lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port="${FOLLOWER_PORT}" \
    --robot.id=so101_follower_unit1

  echo "[Step 2/2] Calibrating SO-101 Leader Arm (Unit 1)..."
  run_cmd lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port="${LEADER_PORT}" \
    --teleop.id=so101_leader_unit1

elif [[ "${MODE}" == "teleop" ]]; then
  CAMERA_JSON="{ wrist: {type: opencv, index_or_path: ${WRIST_CAM_INDEX}, width: 640, height: 480, fps: 30} }"
  echo "[Teleop] Starting Leader -> Follower real-time teleoperation with Wrist Camera..."
  run_cmd lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port="${FOLLOWER_PORT}" \
    --robot.id=so101_follower_unit1 \
    --robot.cameras="${CAMERA_JSON}" \
    --teleop.type=so101_leader \
    --teleop.port="${LEADER_PORT}" \
    --teleop.id=so101_leader_unit1 \
    --display_data=true
else
  echo "Invalid --mode '${MODE}'. Choose 'calibrate' or 'teleop'."
  exit 1
fi
