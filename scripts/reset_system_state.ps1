param(
    [switch]$Confirm,
    [switch]$NoInput,
    [switch]$SkipRedisValidation,
    [switch]$StrictRuntimeValidation,
    [switch]$WithDemoUsers,
    [switch]$SkipSchemaRebuild,
    [switch]$SkipRuntimeClean,
    [switch]$SkipSeed,
    [switch]$AllowProduction,
    [string]$AdminEmail,
    [string]$AdminPassword
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backendDir = Join-Path $repoRoot "backend"

if (-not $Confirm) {
    throw "Refusing to reset. Re-run with -Confirm."
}

Push-Location $backendDir
try {
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        . ".\venv\Scripts\Activate.ps1"
    }

    $argsList = @("manage.py", "full_reset", "--confirm")
    if ($NoInput) { $argsList += "--no-input" }
    if ($SkipRedisValidation) { $argsList += "--skip-redis-validation" }
    if ($StrictRuntimeValidation) { $argsList += "--strict-runtime-validation" }
    if ($WithDemoUsers) { $argsList += "--with-demo-users" }
    if ($SkipSchemaRebuild) { $argsList += "--skip-schema-rebuild" }
    if ($SkipRuntimeClean) { $argsList += "--skip-runtime-clean" }
    if ($SkipSeed) { $argsList += "--skip-seed" }
    if ($AllowProduction) { $argsList += "--allow-production" }
    if ($AdminEmail) { $argsList += "--admin-email", $AdminEmail }
    if ($AdminPassword) { $argsList += "--admin-password", $AdminPassword }

    python @argsList
}
finally {
    Pop-Location
}
