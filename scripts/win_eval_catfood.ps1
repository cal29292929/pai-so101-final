# Cat-food transfer task: run trained ACT policy autonomously and record eval episodes
# Usage: powershell -File scripts\win_eval_catfood.ps1 [-Episodes 3] [-Checkpoint last]
param(
    [int]$Episodes = 3,
    [int]$EpisodeSec = 25,
    [int]$ResetSec = 10,
    [string]$Checkpoint = "last"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
$run = Get-ChildItem (Join-Path $root "outputs\train") -Directory | Sort-Object LastWriteTime | Select-Object -Last 1
$policy = Join-Path $run.FullName "checkpoints\$Checkpoint\pretrained_model"
$evalRoot = Join-Path $env:USERPROFILE (".cache\huggingface\lerobot\local\eval_so101_catfood_" + (Get-Date -Format "yyyyMMdd_HHmm"))

& $py -m lerobot.scripts.lerobot_record `
    "--robot.type=so101_follower" `
    "--robot.port=COM7" `
    "--robot.id=so101_follower_unit1" `
    "--robot.max_relative_target=10" `
    "--robot.cameras={ wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30} }" `
    "--policy.path=$policy" `
    "--policy.device=cpu" `
    "--dataset.repo_id=local/eval_so101_catfood" `
    "--dataset.root=$evalRoot" `
    "--dataset.single_task=Scoop cat food from the blue bowl and drop it into the red bowl." `
    "--dataset.num_episodes=$Episodes" `
    "--dataset.episode_time_s=$EpisodeSec" `
    "--dataset.reset_time_s=$ResetSec" `
    "--dataset.push_to_hub=false" `
    "--display_data=false"
