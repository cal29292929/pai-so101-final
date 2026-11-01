# Cat-food transfer task: teleop demo recording (Windows / lerobot 0.6.1)
# Usage: powershell -File scripts\win_record_catfood.ps1 [-Episodes 15] [-Resume]
param(
    [int]$Episodes = 15,
    [int]$EpisodeSec = 20,
    [int]$ResetSec = 8,
    [switch]$Resume
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

$args_ = @(
    "-m", "lerobot.scripts.lerobot_record",
    "--robot.type=so101_follower",
    "--robot.port=COM7",
    "--robot.id=so101_follower_unit1",
    "--robot.max_relative_target=10",
    "--robot.cameras={ wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30} }",
    "--teleop.type=so101_leader",
    "--teleop.port=COM8",
    "--teleop.id=so101_leader_unit1",
    "--dataset.repo_id=local/so101_catfood_transfer",
    "--dataset.single_task=Scoop cat food from the blue bowl and drop it into the red bowl.",
    "--dataset.num_episodes=$Episodes",
    "--dataset.episode_time_s=$EpisodeSec",
    "--dataset.reset_time_s=$ResetSec",
    "--dataset.push_to_hub=false",
    "--display_data=false"
)
if ($Resume) {
    # Append to the most recent catfood dataset instead of creating a new timestamped one
    $last = Get-ChildItem "$env:USERPROFILE\.cache\huggingface\lerobot\local" -Directory -Filter "so101_catfood_transfer*" |
        Sort-Object LastWriteTime | Select-Object -Last 1
    $args_ += @("--resume=true", "--dataset.root=$($last.FullName)")
}
& $py @args_
