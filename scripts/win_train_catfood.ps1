# Cat-food transfer task: train ACT on CPU (Windows / lerobot 0.6.1)
# Usage: powershell -File scripts\win_train_catfood.ps1 [-Steps 6000]
param(
    [int]$Steps = 6000,
    [int]$BatchSize = 4
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
$data = Get-ChildItem "$env:USERPROFILE\.cache\huggingface\lerobot\local" -Directory -Filter "so101_catfood_transfer*" |
    Sort-Object LastWriteTime | Select-Object -Last 1
$out = Join-Path $root ("outputs\train\act_catfood_" + (Get-Date -Format "yyyyMMdd_HHmm"))

& $py -m lerobot.scripts.lerobot_train `
    "--dataset.repo_id=local/so101_catfood_transfer" `
    "--dataset.root=$($data.FullName)" `
    "--policy.type=act" `
    "--policy.device=cpu" `
    "--policy.push_to_hub=false" `
    "--output_dir=$out" `
    "--job_name=act_catfood" `
    "--steps=$Steps" `
    "--batch_size=$BatchSize" `
    "--num_workers=0" `
    "--save_freq=1000" `
    "--log_freq=50" `
    "--wandb.enable=false"
