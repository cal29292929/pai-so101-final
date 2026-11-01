# Cat-food transfer task: run trained ACT policy autonomously and record eval episodes
# Usage: powershell -File scripts\win_eval_catfood.ps1 [-Episodes 3] [-Checkpoint 001000] [-MaxRelTarget 5] [-LimitScale 0.8] [-EmaAlpha 0.3] [-StallSec 4]
# Runs through scripts\safe_rollout.py: joint targets are clamped to configs\so101_task_config.yaml
# safety.joint_limits_deg x LimitScale, and per-step motion is capped by MaxRelTarget (deg) to move slowly.
# Policy output is EMA-smoothed (EmaAlpha), kept above configs\floor_pose_catfood.yaml if present, and an
# episode is ended early when the joints stay still for StallSec seconds. Start / reset / end all go to
# configs\home_pose_catfood.yaml by lifting with shoulder_lift + elbow_flex first, then moving the pan.
param(
    [int]$Episodes = 3,
    [int]$EpisodeSec = 25,
    [int]$ResetSec = 10,
    [string]$Checkpoint = "last",
    [int]$WristCam = 2,
    [int]$MaxRelTarget = 5,
    [double]$LimitScale = 0.8,
    [double]$EmaAlpha = 0.3,
    [double]$StallSec = 4
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
$run = Get-ChildItem (Join-Path $root "outputs\train") -Directory | Sort-Object LastWriteTime | Select-Object -Last 1
$policy = Join-Path $run.FullName "checkpoints\$Checkpoint\pretrained_model"
$evalRoot = Join-Path $env:USERPROFILE (".cache\huggingface\lerobot\local\rollout_so101_catfood_" + (Get-Date -Format "yyyyMMdd_HHmm"))
$task = "Scoop cat food from the blue bowl and drop it into the red bowl."

# Start from the saved home pose (configs\home_pose_catfood.yaml, made by win_jog_and_home.py --save-home).
# Moves slowly and asks for Enter after printing the joint plan.
if (-not (Test-Path (Join-Path $root "configs\home_pose_catfood.yaml"))) {
    throw "configs\home_pose_catfood.yaml not found: jog above the blue bowl and run win_jog_and_home.py --save-home first"
}
& $py (Join-Path $root "scripts\win_jog_and_home.py") --goto-home
if ($LASTEXITCODE -ne 0) { throw "goto-home failed or aborted" }

# lerobot 0.6.1 runs policies via lerobot-rollout (lerobot-record no longer accepts --policy.*)
& $py (Join-Path $root "scripts\safe_rollout.py") `
    "--limit-scale=$LimitScale" `
    "--ema-alpha=$EmaAlpha" `
    "--stall-s=$StallSec" `
    "--strategy.type=episodic" `
    "--policy.path=$policy" `
    "--device=cpu" `
    "--robot.type=so101_follower" `
    "--robot.port=COM7" `
    "--robot.id=so101_follower_unit1" `
    "--robot.max_relative_target=$MaxRelTarget" `
    "--robot.disable_torque_on_disconnect=false" `
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
