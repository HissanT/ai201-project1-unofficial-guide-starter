$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$venvPython = [System.IO.Path]::GetFullPath($venvPython)

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment Python not found at: $venvPython"
}

& $venvPython (Join-Path $PSScriptRoot "app.py")
