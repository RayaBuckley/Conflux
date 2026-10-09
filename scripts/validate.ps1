[CmdletBinding()]
param(
    [string] $Python = "",
    [ValidateSet("quick", "standard", "full")]
    [string] $Tier = "full"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = if ($Python) { $Python } else { Join-Path $repoRoot ".venv\Scripts\python.exe" }

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Conflux Python not found. Run .\scripts\setup.ps1 or pass -Python."
}

& $venvPython (Join-Path $PSScriptRoot "validate.py") --tier $Tier
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
