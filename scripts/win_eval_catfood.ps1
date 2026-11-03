# Cat-food transfer task: run trained ACT policy autonomously and record eval episodes
# Usage: powershell -File scripts\win_eval_catfood.ps1 [-Episodes 3] [-Checkpoint 001000]
param(
    [int]$Episodes = 3,
    [int]$EpisodeSec = 25,
    [int]$ResetSec = 10,
    [string]$Checkpoint = "last",
    [int]$WristCam = 1
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
$run = Get-ChildItem (Join-Path $root "outputs\train") -Directory | Sort-Object LastWriteTime | Select-Object -Last 1
$policy = Join-Path $run.FullName "checkpoints\$Checkpoint\pretrained_model"
$evalRoot = Join-Path $env:USERPROFILE (".cache\huggingface\lerobot\local\rollout_so101_catfood_" + (Get-Date -Format "yyyyMMdd_HHmm"))
$task = "Scoop cat food from the blue bowl and drop it into the red bowl."

# Park over the blue bowl first: rollout captures the startup pose as its reset target
& $py (Join-Path $PSScriptRoot "win_goto_start.py") COM7

# lerobot 0.6.1 runs policies via lerobot-rollout (lerobot-record no longer accepts --policy.*)
& $py -m lerobot.scripts.lerobot_rollout `
    "--strategy.type=episodic" `
    "--strategy.reset_to_initial_position=true" `
    "--policy.path=$policy" `
    "--device=cpu" `
    "--robot.type=so101_follower" `
    "--robot.port=COM7" `
    "--robot.id=so101_follower_unit1" `
    "--robot.max_relative_target=10" `
    "--robot.cameras={ wrist: {type: opencv, index_or_path: $WristCam, width: 640, height: 480, fps: 30} }" `
    "--task=$task" `
    "--dataset.repo_id=local/rollout_so101_catfood" `
    "--dataset.root=$evalRoot" `
    "--dataset.single_task=$task" `
    "--dataset.num_episodes=$Episodes" `
    "--dataset.episode_time_s=$EpisodeSec" `
    "--dataset.reset_time_s=$ResetSec" `
    "--dataset.push_to_hub=false" `
    "--display_data=false"
