Set-StrictMode -Version Latest

function Test-AiSecretLikeEnvName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $UpperName = $Name.ToUpperInvariant()
    if ($UpperName -eq "OPENAI_API_KEY") { return $true }
    if ($UpperName -eq "ANTHROPIC_API_KEY") { return $true }
    if ($UpperName -eq "GOOGLE_API_KEY") { return $true }
    if ($UpperName -eq "CLOUDFLARE_TUNNEL_TOKEN") { return $true }

    return (
        $UpperName -like "*_SECRET*" -or
        $UpperName -like "*_TOKEN*" -or
        $UpperName -like "*_KEY*" -or
        $UpperName -like "*_PASSWORD*"
    )
}

function Test-AiSecretDefaultName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $UpperName = $Name.ToUpperInvariant()
    if ($UpperName -eq "OPENAI_API_KEY") { return $true }
    if ($UpperName -eq "ANTHROPIC_API_KEY") { return $true }
    if ($UpperName -eq "GOOGLE_API_KEY") { return $true }
    if ($UpperName -eq "CLOUDFLARE_TUNNEL_TOKEN") { return $true }
    if ($UpperName -like "*_SECRET") { return $true }
    if ($UpperName -like "*_PASSWORD") { return $true }
    if ($UpperName -like "*_TOKEN") { return $true }
    if ($UpperName -like "*_API_KEY") { return $true }

    return $false
}

function Test-AiEnvFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Env file path is required."
    }

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Env file not found: $Path"
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Get-AiEnvFileEntries {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $Entries = New-Object System.Collections.Generic.List[object]
    foreach ($Line in Get-Content -LiteralPath $Path) {
        if ([string]::IsNullOrWhiteSpace($Line)) {
            continue
        }

        $Trimmed = $Line.TrimStart()
        if ($Trimmed.StartsWith("#")) {
            continue
        }

        if ($Trimmed -match '^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $Name = $Matches[1]
            $Value = $Matches[2].Trim()

            if ($Value.Length -ge 2) {
                $First = $Value[0]
                $Last = $Value[$Value.Length - 1]
                if (($First -eq '"' -and $Last -eq '"') -or ($First -eq "'" -and $Last -eq "'")) {
                    $Value = $Value.Substring(1, $Value.Length - 2)
                }
            }

            $Entries.Add([pscustomobject]@{
                Name  = $Name
                Value = $Value
            })
        }
    }

    return $Entries
}

function Import-AiEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [switch]$OnlyIfMissing
    )

    $ResolvedPath = Test-AiEnvFilePath -Path $Path
    $Entries = Get-AiEnvFileEntries -Path $ResolvedPath
    $Imported = New-Object System.Collections.Generic.List[string]

    foreach ($Entry in $Entries) {
        $Current = [Environment]::GetEnvironmentVariable($Entry.Name, [EnvironmentVariableTarget]::Process)
        if ([string]::IsNullOrWhiteSpace($Current)) {
            [Environment]::SetEnvironmentVariable($Entry.Name, $Entry.Value, [EnvironmentVariableTarget]::Process)
            $Imported.Add($Entry.Name)
        }
    }

    return $Imported.ToArray()
}

function Write-AiEnvDefaults {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Defaults,
        [switch]$OnlyMissing
    )

    $Directory = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($Directory) -and -not (Test-Path -LiteralPath $Directory)) {
        New-Item -ItemType Directory -Force -Path $Directory | Out-Null
    }

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        New-Item -ItemType File -Force -Path $Path | Out-Null
    }

    $ExistingKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($Entry in Get-AiEnvFileEntries -Path $Path) {
        [void]$ExistingKeys.Add($Entry.Name)
    }

    $Appended = New-Object System.Collections.Generic.List[string]
    foreach ($Key in $Defaults.Keys) {
        $Name = [string]$Key
        if (Test-AiSecretDefaultName -Name $Name) {
            continue
        }

        if ($ExistingKeys.Contains($Name)) {
            continue
        }

        $Value = [string]$Defaults[$Key]
        Add-Content -LiteralPath $Path -Value ("{0}={1}" -f $Name, $Value)
        $Appended.Add($Name)
    }

    return $Appended.ToArray()
}

function Get-AiSafeEnvSummary {
    param(
        [string[]]$Keys = @(
            "AI_PROVIDER",
            "OPENAI_ENABLE_LIVE_TESTS",
            "OPENAI_LIVE_TEST_BUDGET_CENTS",
            "AI_MAX_OUTPUT_TOKENS",
            "AI_PROVIDER_CALLS_ENABLED",
            "AI_PROVIDER_GLOBAL_DISABLE",
            "AI_PROVIDER_BUDGET_MODE",
            "AI_29_30_REGRESSION_LIVE",
            "OPENAI_MODEL",
            "OPENAI_FALLBACK_MODEL",
            "OPENAI_API_KEY"
        )
    )

    foreach ($Key in $Keys) {
        $Value = [Environment]::GetEnvironmentVariable($Key, [EnvironmentVariableTarget]::Process)
        if ([string]::IsNullOrWhiteSpace($Value)) {
            "{0}=missing" -f $Key
            continue
        }

        if (Test-AiSecretLikeEnvName -Name $Key) {
            "{0}=redacted-present" -f $Key
            continue
        }

        "{0}={1}" -f $Key, $Value
    }
}
