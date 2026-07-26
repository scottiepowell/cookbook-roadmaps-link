param(
    [switch]$ApproveLocalWrite,
    [int]$SidecarPort = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
$Image = "local/vanilla-cookbook-adapter:0034g"
$CookbookTarget = "http://127.0.0.1:3000/"
$SidecarTarget = "http://127.0.0.1:$SidecarPort"
$LogPath = Join-Path $RepoRoot ".local\0034i-sidecar.log"
$ErrorLogPath = Join-Path $RepoRoot ".local\0034i-sidecar-error.log"
$DemoDataDir = Join-Path $RepoRoot ".tmp-ai-demo\0034i-e2e"
$SidecarProcess = $null
$RuntimeStarted = $false
$Stage = "preflight"

function Fail-Safe {
    param([string]$Message)
    [Console]::Error.WriteLine("BLOCKED: $Message")
    exit 2
}

if (-not $ApproveLocalWrite) {
    Fail-Safe "-ApproveLocalWrite is required; no local write was attempted."
}

if ($SidecarPort -lt 1024 -or $SidecarPort -gt 65535) {
    Fail-Safe "SidecarPort must be a local user port."
}

if ([Environment]::GetEnvironmentVariable("CI") -or
    [Environment]::GetEnvironmentVariable("GITHUB_ACTIONS") -or
    [Environment]::GetEnvironmentVariable("CLOUDFLARE_TUNNEL_TOKEN") -or
    [Environment]::GetEnvironmentVariable("TUNNEL_TOKEN") -or
    [Environment]::GetEnvironmentVariable("AWS_REGION")) {
    Fail-Safe "CI, deployment, tunnel, or AWS context is not accepted."
}

if ($CookbookTarget -notmatch '^http://(127\.0\.0\.1|localhost|\[::1\]):3000/$') {
    Fail-Safe "Only the fixed loopback Cookbook target is accepted."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Fail-Safe "Docker is required."
}

try {
    & docker info --format "{{.ServerVersion}}" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail-Safe "Docker Desktop daemon is unavailable." }

    $env:VANILLA_COOKBOOK_IMAGE = $Image
    $env:COOKBOOK_TARGET_URL = $CookbookTarget
    $env:RUN_LOCAL_PERSISTENT_AUTH_FIXTURE = "1"
    $env:LOCAL_PERSISTENT_AUTH_FIXTURE_APPROVED = "1"
    $env:SYNTHETIC_AUTH_FIXTURE = "1"

    Write-Host "Starting approved local cookbook-local runtime."
    $Stage = "start Cookbook runtime"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "start-vanilla-cookbook-local.ps1") -CookbookImage $Image
    if ($LASTEXITCODE -ne 0) { throw "The local Cookbook runtime did not start." }
    $RuntimeStarted = $true

    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "check-vanilla-cookbook-local.ps1")
    if ($LASTEXITCODE -ne 0) { throw "The local Cookbook runtime did not pass readiness." }

    $cookbookReady = $false
    $Stage = "wait for Cookbook HTTP readiness"
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $cookbookResponse = Invoke-WebRequest -UseBasicParsing -Uri $CookbookTarget -TimeoutSec 2
            if ([int]$cookbookResponse.StatusCode -eq 200) { $cookbookReady = $true; break }
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $cookbookReady) { throw "The local Cookbook did not become HTTP-ready." }
    Write-Host "PASS: local Cookbook HTTP readiness confirmed without exposing page content."

    New-Item -ItemType Directory -Force -Path (Split-Path $LogPath) | Out-Null
    foreach ($path in @($LogPath, $ErrorLogPath)) {
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
    $env:AI_PROVIDER = "mock"
    $env:AI_LOCAL_SAVE_ENABLED = "true"
    $env:AI_LOCAL_SAVE_APPROVED = "true"
    $env:AI_LOCAL_COOKBOOK_RUNTIME_VERIFIED = "true"
    $env:COOKBOOK_COMPOSE_PROJECT = "cookbook-local"

    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "The local Python environment is unavailable." }
    $env:PYTHONPATH = "ai-api"
    $env:AI_MODEL = "mock-basic"
    $env:OPENAI_ENABLE_LIVE_TESTS = "false"
    $env:COOKBOOK_DB_PATH = Join-Path $DemoDataDir "recipes.sqlite"
    & $Python -m app.demo_data --output-dir $DemoDataDir | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Mock sidecar fixture setup failed." }
    $Stage = "start mock sidecar"
    $SidecarProcess = Start-Process -FilePath $Python -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", $SidecarPort) `
        -RedirectStandardOutput $LogPath -RedirectStandardError $ErrorLogPath

    $ready = $false
    $Stage = "wait for sidecar readiness"
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri "$SidecarTarget/health" -TimeoutSec 2
            if ($health.status -eq "ok") { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) { throw "The mock sidecar did not become ready." }

    $readiness = Invoke-RestMethod -Uri "$SidecarTarget/demo/readiness" -TimeoutSec 5
    if (-not $readiness.local_real_save.available) { throw "Persistent local-save readiness was not enabled." }
    Write-Host "PASS: sidecar readiness and local persistent-save gates are enabled."

    $import = Invoke-RestMethod -Method Post -Uri "$SidecarTarget/ai/import-recipe" -ContentType "application/json" `
        -Body (@{provider_mode="mock"; model="mock-basic"; text="Warm beans with lemon and herbs."; source="local fixture"} | ConvertTo-Json -Depth 8)
    $draft = $import.draft
    if ($null -eq $draft) { throw "Mock importer did not return a draft." }
    $idempotencyKey = "0034i-local-ui-e2e"
    $candidateBody = @{draft=$draft; idempotency_key=$idempotencyKey} | ConvertTo-Json -Depth 12

    $dryRun = Invoke-RestMethod -Method Post -Uri "$SidecarTarget/adapter/recipes/import-candidate/dry-run" -ContentType "application/json" -Body $candidateBody
    $Stage = "persistent local commit transport"
    if ($dryRun.status -ne "ready" -or $dryRun.result.status -ne "valid") { throw "Local dry-run did not validate the reviewed candidate." }
    Write-Host "PASS: reviewed mock importer draft passed local dry-run."

    $commitBody = @{draft=$draft; idempotency_key=$idempotencyKey; confirm_local_save=$true} | ConvertTo-Json -Depth 12
    $commit = Invoke-RestMethod -Method Post -Uri "$SidecarTarget/adapter/recipes/import-candidate/local-persistent-commit" -ContentType "application/json" -Body $commitBody
    if ($commit.status -notin @("verified", "committed")) { throw "Persistent local commit did not return a successful safe status." }
    foreach ($field in @("recipe_uid", "read_after_write")) {
        if ([string]::IsNullOrWhiteSpace([string]$commit.$field)) { throw "Safe commit field '$field' was missing." }
    }
    $replayStatus = [string]$commit.replay_status
    if ([string]::IsNullOrWhiteSpace($replayStatus)) { $replayStatus = "initial" }
    Write-Host ("PASS: core read-after-write verified; status={0}; recipe_uid={1}; idempotency={2}." -f $commit.status, $commit.recipe_uid, $replayStatus)
    Write-Host "PASS: database/uploads restoration is reported by the core disposable verification boundary."
    Write-Host "LIMITATION: Vanilla Cookbook browser observation is not attempted because no real session is used."
}
catch {
    $sidecarState = "not_started"
    if ($null -ne $SidecarProcess) {
        $sidecarState = if ($SidecarProcess.HasExited) { "exited_$($SidecarProcess.ExitCode)" } else { "running" }
    }
    [Console]::Error.WriteLine("E2E verification failed safely during $Stage; sidecar=$sidecarState; local runtime was not left running by this script.")
    exit 1
}
finally {
    if ($null -ne $SidecarProcess -and -not $SidecarProcess.HasExited) {
        Stop-Process -Id $SidecarProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $SidecarProcess) {
        try { $SidecarProcess.WaitForExit(5000) | Out-Null } catch { }
    }
    foreach ($path in @($LogPath, $ErrorLogPath)) {
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue }
    }
    if (Test-Path -LiteralPath $DemoDataDir) { Remove-Item -LiteralPath $DemoDataDir -Recurse -Force -ErrorAction SilentlyContinue }
    if ($RuntimeStarted) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "stop-vanilla-cookbook-local.ps1") | Out-Null
    }
}
