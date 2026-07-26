[CmdletBinding()]
param(
    [switch] $CoverageOnly,
    [switch] $NoCoverage,
    [switch] $AuditOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Conflux virtual environment not found at $venvPython. Run .\scripts\setup.ps1 first."
}

function Invoke-Check {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    Write-Host "[validate] $Name"
    & $venvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Push-Location $repoRoot
try {
    Invoke-Check -Name "repository audit" -Arguments @("scripts\audit_repository.py")
    if ($AuditOnly) {
        return
    }

    $pytestArguments = @("-m", "pytest")
    if (-not $NoCoverage) {
        $pytestArguments += @("--cov=src/conflux", "--cov-report=term-missing", "--cov-report=html")
    }
    Invoke-Check -Name "pytest" -Arguments $pytestArguments

    if (-not $CoverageOnly) {
        Invoke-Check -Name "ruff" -Arguments @("-m", "ruff", "check", "src", "tests")
        Invoke-Check -Name "mypy" -Arguments @("-m", "mypy", "src")
    }
}
finally {
    Pop-Location
}

Write-Host "[validate] All checks passed"
