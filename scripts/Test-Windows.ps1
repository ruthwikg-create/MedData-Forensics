$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run Setup-Windows.ps1 first." }
& $Python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "Test dependencies failed" }
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed; do not report a successful build." }
