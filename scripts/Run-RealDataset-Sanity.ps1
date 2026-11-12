$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run RUN_ME_WINDOWS.bat first to install dependencies." }
Write-Host "PneumoniaMNIST license: CC BY 4.0; download official dataset from Zenodo." -ForegroundColor Cyan
Write-Host "Research smoke test only. No clinical validation or patient-level independence claim." -ForegroundColor Yellow
& $Python scripts\validate_real_dataset.py --download-pneumoniamnist --max-per-split 600
if ($LASTEXITCODE -ne 0) { throw "Research dataset smoke test failed; review error before claiming results." }
