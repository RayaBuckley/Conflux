[CmdletBinding()]
param(
    [string] $Python = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = if ($Python) { $Python } else { Join-Path $repoRoot ".venv\Scripts\python.exe" }

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Conflux Python not found. Run .\scripts\setup.ps1 or pass -Python."
}

& $venvPython (Join-Path $PSScriptRoot "validate.py")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
