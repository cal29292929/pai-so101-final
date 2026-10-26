#!/usr/bin/env bash
# ==============================================================================
# 第5回講義のデータ収集原則を組み込んだ LeRobot データセット記録スクリプト
# - 原則1: 毎回必ず同じ初期姿勢 (Reset pose) から記録を開始する (OOD防止)
# - 原則2: グリッパの開閉は 0 / 1 を明確にし、対象物把持の瞬間をはっきりさせる
# - 原則3: エピソード途中で「停止（迷い）」を作らない
# - 原則4: 軌道を一意にする（ACT等の多峰性による平均化失敗を防ぐ）
# ==============================================================================
set -euo pipefail

MODE="${1:-single}"
REPO_ID="${REPO_ID:-local/so101_wrist_pick_sort}"
NUM_EPISODES="${NUM_EPISODES:-40}"
EPISODE_TIME_S="${EPISODE_TIME_S:-25}"
RESET_TIME_S="${RESET_TIME_S:-10}"
TASK_DESC="${TASK_DESC:-Pick up the target block using wrist camera feedback and place it into the target tray.}"

echo "============================================================"
echo "LeRobot Dataset Recording Guide (${MODE})"
echo "Repo ID       : ${REPO_ID}"
echo "Episodes      : ${NUM_EPISODES}"
echo "Task          : ${TASK_DESC}"
echo "============================================================"

cat << REC_EOF

# Run the following command to record the dataset:
lerobot-record \\
  --robot.type=so101_follower \\
  --robot.port=\${FOLLOWER_PORT:-/dev/ttyACM1} \\
  --robot.id=so101_follower_arm1 \\
  --robot.cameras="{ wrist: {type: opencv, index_or_path: \${WRIST_CAM:-0}, width: 640, height: 480, fps: 30}, top: {type: opencv, index_or_path: \${TOP_CAM:-2}, width: 640, height: 480, fps: 30} }" \\
  --teleop.type=so101_leader \\
  --teleop.port=\${LEADER_PORT:-/dev/ttyACM0} \\
  --teleop.id=so101_leader_arm1 \\
  --dataset.repo_id=${REPO_ID} \\
  --dataset.num_episodes=${NUM_EPISODES} \\
  --dataset.episode_time_s=${EPISODE_TIME_S} \\
  --dataset.reset_time_s=${RESET_TIME_S} \\
  --dataset.single_task="${TASK_DESC}" \\
  --dataset.push_to_hub=false \\
  --display_data=true

# After recording, always run RoboOps validation:
python3 scripts/03_validate_and_debug_dataset.py --dataset-dir ~/.cache/huggingface/lerobot/${REPO_ID}
REC_EOF
