# Requires: PowerShell 5.1+
# Usage: From repo root, run: scripts\setup_environment.ps1

param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) {
    Write-Host "[setup] $msg" -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "[setup] $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "[setup] $msg" -ForegroundColor Yellow
}

# Resolve repo root as the parent of this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

$VenvPath = Join-Path $RepoRoot ".venv"

Write-Info "Using Python: $PythonExe"

if (-Not (Test-Path $VenvPath)) {
    Write-Info "Creating virtual environment at $VenvPath"
    & $PythonExe -m venv $VenvPath
} else {
    Write-Warn "Virtual environment already exists at $VenvPath (reusing)"
}

Write-Info "Activating virtual environment"
$ActivateScript = Join-Path $VenvPath "Scripts/Activate.ps1"
if (-Not (Test-Path $ActivateScript)) {
    throw "Activate script not found at $ActivateScript"
}
& $ActivateScript

Write-Info "Upgrading pip"
python -m pip install --upgrade pip

Write-Info "Installing dependencies from requirements.txt"
python -m pip install -r requirements.txt

Write-Info "Verifying key imports"
python -c "import pandas, numpy, pyarrow, swisseph, matplotlib, tqdm; print('Environment OK')"

Write-Ok "Environment ready. To activate later: .\.venv\Scripts\Activate.ps1"
Write-Ok "Run relocation pilot with: python scripts/generate_relocation_field.py"