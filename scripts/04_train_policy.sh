#!/usr/bin/env bash
# ==============================================================================
# LeRobot 方策学習スクリプト (ACT / Diffusion Policy / SmolVLA)
# 第2回講義（学習条件・seed・Dataset revisionの記録）＋第5回・第6回講義対応
# Usage:
#   bash scripts/04_train_policy.sh act
#   bash scripts/04_train_policy.sh diffusion
#   bash scripts/04_train_policy.sh smolvla
# ==============================================================================
set -euo pipefail

POLICY_TYPE="${1:-act}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/so101_wrist_pick_sort}"
SEED="${SEED:-42}"
STEPS="${STEPS:-30000}"
OUTPUT_DIR="outputs/train/${POLICY_TYPE}_so101_seed${SEED}"

echo "============================================================"
echo "Training Policy : ${POLICY_TYPE}"
echo "Dataset Repo ID : ${DATASET_REPO_ID}"
echo "Output Dir      : ${OUTPUT_DIR}"
echo "Seed            : ${SEED}"
echo "============================================================"

if [ "${POLICY_TYPE}" = "act" ]; then
  cat << CMD_EOF
# Train ACT (Action Chunking with Transformers) — Fast & sample-efficient baseline (30-50 episodes):
WANDB_MODE=\${WANDB_MODE:-offline} lerobot-train \\
  --dataset.repo_id=${DATASET_REPO_ID} \\
  --policy.type=act \\
  --output_dir=${OUTPUT_DIR} \\
  --job_name=act_so101_single \\
  --policy.device=cuda \\
  --seed=${SEED} \\
  --steps=${STEPS} \\
  --batch_size=16 \\
  --wandb.enable=true
CMD_EOF

elif [ "${POLICY_TYPE}" = "diffusion" ]; then
  cat << CMD_EOF
# Train Diffusion Policy — Strong for multimodal trajectories (comparison model):
WANDB_MODE=\${WANDB_MODE:-offline} lerobot-train \\
  --dataset.repo_id=${DATASET_REPO_ID} \\
  --policy.type=diffusion \\
  --output_dir=${OUTPUT_DIR} \\
  --job_name=diffusion_so101_single \\
  --policy.device=cuda \\
  --seed=${SEED} \\
  --steps=${STEPS} \\
  --batch_size=16 \\
  --wandb.enable=true
CMD_EOF

elif [ "${POLICY_TYPE}" = "smolvla" ]; then
  cat << CMD_EOF
# Fine-tune SmolVLA (450M Open-Source VLA introduced in Lecture 5 & 6):
WANDB_MODE=\${WANDB_MODE:-offline} lerobot-train \\
  --dataset.repo_id=${DATASET_REPO_ID} \\
  --policy.path=lerobot/smolvla_base \\
  --output_dir=${OUTPUT_DIR} \\
  --job_name=smolvla_so101_finetune \\
  --policy.device=cuda \\
  --seed=${SEED} \\
  --steps=20000 \\
  --batch_size=8 \\
  --wandb.enable=true
CMD_EOF
else
  echo "Unknown policy type: ${POLICY_TYPE}. Choose from: act | diffusion | smolvla"
  exit 1
fi
