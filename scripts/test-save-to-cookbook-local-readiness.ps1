param(
    [switch]$ApproveLocalWrite,
    [string]$CookbookTargetUrl = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"
if ($null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location $RepoRoot
$ComposeFile = Join-Path $RepoRoot "docker-compose.local.yml"
$ComposeProject = "cookbook-local"
$RuntimeRoot = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot ".local\vanilla-cookbook"))
$DbPath = Join-Path $RuntimeRoot "db\dev.sqlite"
$UploadsPath = Join-Path $RuntimeRoot "uploads"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Target = $CookbookTargetUrl
if ([string]::IsNullOrWhiteSpace($Target)) {
    $Target = [Environment]::GetEnvironmentVariable("COOKBOOK_TARGET_URL")
}
if ([string]::IsNullOrWhiteSpace($Target)) {
    $Target = "http://127.0.0.1:3000/"
}

$BackupRoot = $null
$BackupDb = $null
$BackupUploads = $null
$BackupCreated = $false
$AppWasRunning = $false
$HarnessSucceeded = $false
$RestoreSucceeded = $false
$ExitCode = 0
$Stage = "preflight"

function Stop-WithSafeError {
    param([string]$Message)
    throw $Message
}

function Assert-LocalTarget {
    if ($Target -match "cookbook\.roadmaps\.link|cloudflare|tunnel|aws|github|production|deploy") {
        Stop-WithSafeError "target is not an approved local target"
    }
    try {
        $Uri = [System.Uri]$Target
    } catch {
        Stop-WithSafeError "target is not a valid local URL"
    }
    if (-not $Uri.IsAbsoluteUri -or $Uri.Scheme -ne "http" -or $Uri.Host -notin @("127.0.0.1", "localhost", "::1")) {
        Stop-WithSafeError "target is not loopback HTTP"
    }
    if ($Uri.Port -ne 3000) {
        Stop-WithSafeError "target is not the local Cookbook port"
    }
}

function Assert-WithinRuntime {
    param([string]$PathValue)
    $Resolved = [System.IO.Path]::GetFullPath($PathValue)
    $Prefix = $RuntimeRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $Resolved.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-WithSafeError "runtime path is outside the ignored local runtime"
    }
}

function Invoke-ComposeQuiet {
    param([string[]]$Arguments)
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Docker compose @Arguments 2>$null 1>$null
    $ComposeExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
    if ($ComposeExitCode -ne 0 -and $Arguments -notcontains "stop") {
        Stop-WithSafeError "local Compose command failed"
    }
}

if (-not $ApproveLocalWrite) {
    Write-Host "REFUSED: explicit -ApproveLocalWrite is required; no local write was attempted."
    exit 2
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "REFUSED: Docker is unavailable; no local write was attempted."
    exit 2
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    Write-Host "REFUSED: repository Python runtime is unavailable; no local write was attempted."
    exit 2
}

$Docker = (Get-Command docker).Source
try {
    Assert-LocalTarget
    $Stage = "runtime preflight"
    if (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable("CLOUDFLARE_TUNNEL_TOKEN"))) {
        Stop-WithSafeError "tunnel configuration is not allowed"
    }
    if (-not (Test-Path -LiteralPath $ComposeFile -PathType Leaf)) {
        Stop-WithSafeError "local Compose file is missing"
    }
    & $Docker info --format "{{.ServerVersion}}" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Stop-WithSafeError "Docker Desktop daemon is unavailable"
    }
    if (-not (Test-Path -LiteralPath $RuntimeRoot -PathType Container) -or
        -not (Test-Path -LiteralPath $DbPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $UploadsPath -PathType Container)) {
        Stop-WithSafeError "ignored disposable runtime paths are incomplete"
    }
    Assert-WithinRuntime -PathValue $DbPath
    Assert-WithinRuntime -PathValue $UploadsPath
    & git check-ignore -q -- ".local\vanilla-cookbook\db\dev.sqlite"
    if ($LASTEXITCODE -ne 0) {
        Stop-WithSafeError "disposable database is not ignored"
    }

    $Services = @(& $Docker compose -p $ComposeProject -f $ComposeFile config --services 2>$null | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($Services.Count -ne 1 -or $Services[0] -ne "app") {
        Stop-WithSafeError "cookbook-local Compose scope is not app-only"
    }
    $AppContainerId = (& $Docker compose -p $ComposeProject -f $ComposeFile ps -q app 2>$null).Trim()
    if ([string]::IsNullOrWhiteSpace($AppContainerId)) {
        Stop-WithSafeError "cookbook-local app is not running"
    }
    $AppRunning = (& $Docker inspect -f "{{.State.Running}}" $AppContainerId 2>$null).Trim()
    if ($AppRunning -ne "true") {
        Stop-WithSafeError "cookbook-local app is not running"
    }
    $AppWasRunning = $true
    $ProjectContainerIds = @(& $Docker ps --filter "label=com.docker.compose.project=$ComposeProject" --quiet 2>$null | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($ProjectContainerIds.Count -ne 1 -or -not $AppContainerId.StartsWith($ProjectContainerIds[0].Trim(), [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-WithSafeError "cookbook-local has a non-app service running"
    }

    $MountsJson = & $Docker inspect --format "{{json .Mounts}}" $AppContainerId 2>$null
    $Mounts = $MountsJson | ConvertFrom-Json
    if ($Mounts.Count -ne 2) {
        Stop-WithSafeError "unexpected local write mounts"
    }
    $ExpectedMounts = @{
        "/app/prisma/db" = [System.IO.Path]::GetFullPath((Join-Path $RuntimeRoot "db"))
        "/app/uploads" = $UploadsPath
    }
    foreach ($Mount in $Mounts) {
        if (-not $ExpectedMounts.ContainsKey($Mount.Destination) -or -not $Mount.RW) {
            Stop-WithSafeError "local write mount is outside approved scope"
        }
        if ([System.IO.Path]::GetFullPath($Mount.Source) -ne $ExpectedMounts[$Mount.Destination]) {
            Stop-WithSafeError "local write mount source is not the ignored runtime"
        }
    }

    $Stage = "localhost readiness probe"
    $Ready = $false
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        try {
            $Probe = Invoke-WebRequest -UseBasicParsing -Uri $Target -TimeoutSec 5
            if ([int]$Probe.StatusCode -ge 200 -and [int]$Probe.StatusCode -lt 400) {
                $Ready = $true
                break
            }
        } catch {
            # The upstream container may need a short startup window. Keep output safe.
        }
        Start-Sleep -Seconds 1
    }
    if (-not $Ready) {
        Stop-WithSafeError "local Cookbook readiness probe failed"
    }

    $BackupRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("cookbook-local-readiness-" + [Guid]::NewGuid().ToString("N"))
    $BackupDb = Join-Path $BackupRoot "db\dev.sqlite"
    $BackupUploads = Join-Path $BackupRoot "uploads"
    New-Item -ItemType Directory -Force -Path (Split-Path $BackupDb), $BackupUploads | Out-Null
    $Stage = "backup"
    $Stage = "backup-stop"
    Invoke-ComposeQuiet -Arguments @("-p", $ComposeProject, "-f", $ComposeFile, "stop", "app")
    $Stage = "backup-stop-query"
    $StoppedStateRaw = @(& $Docker compose -p $ComposeProject -f $ComposeFile ps -q app 2>$null)
    $StoppedState = if ($StoppedStateRaw.Count -gt 0) { ($StoppedStateRaw -join "").Trim() } else { "" }
    if (-not [string]::IsNullOrWhiteSpace($StoppedState)) {
        $Stage = "backup-stop-inspect"
        $StoppedRunning = (& $Docker inspect -f "{{.State.Running}}" $StoppedState 2>$null).Trim()
        if ($StoppedRunning -eq "true") {
            Stop-WithSafeError "local app did not stop before backup"
        }
    }
    $Stage = "backup-database"
    Copy-Item -LiteralPath $DbPath -Destination $BackupDb -Force
    $Stage = "backup-uploads"
    Get-ChildItem -LiteralPath $UploadsPath -Force | Copy-Item -Destination $BackupUploads -Recurse -Force
    $Stage = "backup-verify"
    if (-not (Test-Path -LiteralPath $BackupDb -PathType Leaf) -or -not (Test-Path -LiteralPath $BackupUploads -PathType Container)) {
        Stop-WithSafeError "disposable backup was not created"
    }
    $BackupCreated = $true
    Write-Host "PASS: local-only preflight and disposable backup completed."

    $Stage = "synthetic write and evidence"
    $WriteJson = & $Python (Join-Path $RepoRoot "ai-api\app\local_save_readiness.py") --db $DbPath --mode write 2>$null
    if ($LASTEXITCODE -ne 0) {
        Stop-WithSafeError "synthetic local write failed"
    }
    $WriteResult = $WriteJson | ConvertFrom-Json
    if ($WriteResult.status -ne "write-and-verify-passed" -or
        $WriteResult.serialization_status -ne "round-trip-passed" -or
        $WriteResult.ownership_status -ne "synthetic-owner-passed" -or
        $WriteResult.duplicate_status -ne "duplicate-prevented" -or
        $WriteResult.failure_status -ne "failure-rollback-passed") {
        Stop-WithSafeError "local write evidence did not pass"
    }
    Write-Host ("PASS: one synthetic recipe write and read-only verification passed; recipe id {0}." -f $WriteResult.synthetic_recipe_id)
    Write-Host ("PASS: duplicate/idempotency evidence: {0}." -f $WriteResult.idempotency_status)
    Write-Host ("PASS: injected transaction failure rolled back: {0}." -f $WriteResult.failure_status)

    $Stage = "local read-after-write verification"
    Invoke-ComposeQuiet -Arguments @("-p", $ComposeProject, "-f", $ComposeFile, "up", "-d", "app")
    Start-Sleep -Seconds 3
    $VerifyJson = & $Python (Join-Path $RepoRoot "ai-api\app\local_save_readiness.py") --db $DbPath --mode verify --user-id $WriteResult.synthetic_user_id --recipe-id $WriteResult.synthetic_recipe_id 2>$null
    if ($LASTEXITCODE -ne 0) {
        Stop-WithSafeError "local read-after-write verification failed"
    }
    Write-Host "PASS: local read-after-write verification passed."
    $HarnessSucceeded = $true
} catch {
    $ExitCode = 1
    Write-Host ("FAIL: local readiness evidence did not complete at {0}; disposable restore was attempted." -f $Stage)
} finally {
    if ($BackupCreated) {
        try {
            $Stage = "disposable restore"
            Invoke-ComposeQuiet -Arguments @("-p", $ComposeProject, "-f", $ComposeFile, "stop", "app")
            Copy-Item -LiteralPath $BackupDb -Destination $DbPath -Force
            Remove-Item -LiteralPath $UploadsPath -Recurse -Force
            New-Item -ItemType Directory -Force -Path $UploadsPath | Out-Null
            Get-ChildItem -LiteralPath $BackupUploads -Force | Copy-Item -Destination $UploadsPath -Recurse -Force
            $RestoreSucceeded = $true
            if ($AppWasRunning) {
                Invoke-ComposeQuiet -Arguments @("-p", $ComposeProject, "-f", $ComposeFile, "up", "-d", "app")
            }
            if ($HarnessSucceeded) {
                Write-Host "PASS: disposable DB/uploads restored and local app restarted."
            }
        } catch {
            $RestoreSucceeded = $false
            $ExitCode = 5
            Write-Host "BLOCKED: disposable restore or local app recovery failed; inspect the local runtime before any further write."
        }
        if ($RestoreSucceeded -and $BackupRoot -and (Test-Path -LiteralPath $BackupRoot)) {
            Remove-Item -LiteralPath $BackupRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

if ($HarnessSucceeded -and -not $RestoreSucceeded) {
    $ExitCode = 5
}
exit $ExitCode
