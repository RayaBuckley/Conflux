[CmdletBinding()]
param(
    [ValidateSet("core", "research")]
    [string] $Profile = "core"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPath = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

function Get-PythonCommand {
    $candidates = @(
        @{ Command = $venvPython; Arguments = @() },
        @{ Command = "py"; Arguments = @("-3.12") },
        @{ Command = "python"; Arguments = @() },
        @{ Command = "python3"; Arguments = @() }
    )

    foreach ($candidate in $candidates) {
        if ($candidate.Command -eq $venvPython) {
            $available = Test-Path -LiteralPath $candidate.Command
        } else {
            $available = [bool](Get-Command $candidate.Command -ErrorAction SilentlyContinue)
        }

        if ($available) {
            $versionOutput = & $candidate.Command @($candidate.Arguments) --version 2>&1
            if ($versionOutput -match "Python\s+(\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if (($major -gt 3) -or (($major -eq 3) -and ($minor -ge 12))) {
                    return $candidate
                }
            }
        }
    }

    throw "Python 3.12 or newer was not found. Install Python 3.12+ and rerun scripts\setup.ps1."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Python,
        [Parameter(Mandatory = $false)]
        [string[]] $Arguments = @()
    )

    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code ${LASTEXITCODE}: $Python $($Arguments -join ' ')"
    }
}

function Test-VirtualEnvironmentHealthy {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        return $false
    }

    $cfgPath = Join-Path $venvPath "pyvenv.cfg"
    if (-not (Test-Path -LiteralPath $cfgPath)) {
        return $false
    }

    $cfg = Get-Content -LiteralPath $cfgPath -Raw
    $executableLine = $cfg -split "`r?`n" | Where-Object { $_ -match '^executable\s*=' } | Select-Object -First 1
    if ($executableLine -and $executableLine -match '^executable\s*=\s*(.+)$') {
        try {
            $baseInterpreterExists = Test-Path -LiteralPath $Matches[1].Trim()
        } catch {
            $baseInterpreterExists = $false
        }
        if (-not $baseInterpreterExists) {
            return $false
        }
    }

    try {
        & $venvPython -c "import sys; assert sys.version_info >= (3, 12)" *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

if (Test-Path -LiteralPath $venvPath) {
    if (-not (Test-VirtualEnvironmentHealthy)) {
        Write-Host "[setup] Existing virtual environment is unusable; recreating it"
        Remove-Item -LiteralPath $venvPath -Recurse -Force
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $bootstrap = Get-PythonCommand
    $bootstrapCommand = $bootstrap.Command
    $bootstrapArguments = @($bootstrap.Arguments) + @("-m", "venv", $venvPath)
    Write-Host "[setup] Creating virtual environment at $venvPath"
    Invoke-Python -Python $bootstrapCommand -Arguments $bootstrapArguments
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment creation did not produce $venvPython."
}

Write-Host "[setup] Upgrading packaging tools"
Invoke-Python -Python $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")

$extras = if ($Profile -eq "research") {
    ".[dev,verification,agentdojo,local-model,openai-compatible]"
} else {
    ".[dev]"
}
Write-Host "[setup] Installing Conflux $Profile dependencies"
Invoke-Python -Python $venvPython -Arguments @("-m", "pip", "install", "-e", $extras)

Write-Host "[setup] Installed versions"
Invoke-Python -Python $venvPython -Arguments @("--version")
Invoke-Python -Python $venvPython -Arguments @("-m", "pytest", "--version")
Invoke-Python -Python $venvPython -Arguments @("-m", "ruff", "--version")
Invoke-Python -Python $venvPython -Arguments @("-m", "mypy", "--version")

Write-Host "[setup] Complete ($Profile profile). The environment is available at $venvPath"
