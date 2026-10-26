#!/usr/bin/env bash
# ==============================================================================
# 04_record_and_train_policy.sh
# Phase 2: LeRobot リーダー・フォロワー模倣学習 & RoboOps 品質保証パイプライン
# - Step 1: record   (Leader-Follower + リストカメラでデータセット収集)
# - Step 2: validate (Day1-2 RoboOps 準拠のデータセット品質・安全制限テスト)
# - Step 3: train    (ACT / SmolVLA ポリシーの学習)
# - Step 4: eval     (学習済みポリシーの実機デプロイ・評価)
# ==============================================================================
set -euo pipefail

STEP="validate"
REPO_ID="${REPO_ID:-cal29292929/so101_active_wrist_sorting}"
FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/ttyACM0}"
LEADER_PORT="${LEADER_PORT:-/dev/ttyACM1}"
WRIST_CAM_INDEX="${WRIST_CAM_INDEX:-0}"
NUM_EPISODES="${NUM_EPISODES:-30}"
POLICY_TYPE="${POLICY_TYPE:-act}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --step)
      STEP="$2"
      shift 2
      ;;
    --repo-id)
      REPO_ID="$2"
      shift 2
      ;;
    --episodes)
      NUM_EPISODES="$2"
      shift 2
      ;;
    --policy)
      POLICY_TYPE="$2"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1"
      echo "Usage: $0 [--step record|validate|train|eval|all] [--repo-id cal29292929/so101_active_wrist_sorting] [--episodes 30] [--policy act|smolvla]"
      exit 1
      ;;
  esac
done

CAMERA_JSON="{ wrist: {type: opencv, index_or_path: ${WRIST_CAM_INDEX}, width: 640, height: 480, fps: 30} }"

if [[ "${STEP}" == "record" || "${STEP}" == "all" ]]; then
  echo "[Step 1] Recording ${NUM_EPISODES} demonstration episodes with SO-101 Leader-Follower + Wrist Camera..."
  lerobot-record \
    --robot.type=so101_follower \
    --robot.port="${FOLLOWER_PORT}" \
    --robot.id=so101_follower_unit1 \
    --robot.cameras="${CAMERA_JSON}" \
    --teleop.type=so101_leader \
    --teleop.port="${LEADER_PORT}" \
    --teleop.id=so101_leader_unit1 \
    --dataset.repo_id="${REPO_ID}" \
    --dataset.num_episodes="${NUM_EPISODES}" \
    --dataset.single_task="Inspect object with wrist camera and sort into PASS or HOLD tray" \
    --display_data=true
fi

if [[ "${STEP}" == "validate" || "${STEP}" == "all" ]]; then
  echo "[Step 2] Running RoboOps Dataset & Safety Contract Checks (Day 1-2 MLOps/RoboOps)..."
  pytest -q
fi

if [[ "${STEP}" == "train" || "${STEP}" == "all" ]]; then
  echo "[Step 3] Training LeRobot Policy (${POLICY_TYPE}) on ${REPO_ID}..."
  lerobot-train \
    --dataset.repo_id="${REPO_ID}" \
    --policy.type="${POLICY_TYPE}" \
    --output_dir="outputs/train/${POLICY_TYPE}_so101_wrist" \
    --job_name="${POLICY_TYPE}_so101_wrist" \
    --policy.device=cuda \
    --wandb.enable=true
fi

if [[ "${STEP}" == "eval" || "${STEP}" == "all" ]]; then
  echo "[Step 4] Evaluating trained ${POLICY_TYPE} policy on SO-101 Follower..."
  lerobot-record \
    --robot.type=so101_follower \
    --robot.port="${FOLLOWER_PORT}" \
    --robot.id=so101_follower_unit1 \
    --robot.cameras="${CAMERA_JSON}" \
    --dataset.repo_id="${REPO_ID}_eval" \
    --dataset.num_episodes=10 \
    --dataset.single_task="Autonomous evaluation of trained ACT wrist-camera policy" \
    --policy.path="outputs/train/${POLICY_TYPE}_so101_wrist/checkpoints/last/pretrained_model"
fi
