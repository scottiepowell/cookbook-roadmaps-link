param(
    [string]$Text = "omelet with eggs cheese maybe onions cooked in butter fold it over",
    [Nullable[int]]$MaxOutputTokens = $null,
    [Nullable[double]]$AiTimeoutSeconds = $null,
    [switch]$ProviderDebug
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$CommandArgs = @("scripts\smoke-openai-importer-live.py", "--text", $Text)
if ($PSBoundParameters.ContainsKey("MaxOutputTokens")) {
    $CommandArgs += @("--max-output-tokens", $MaxOutputTokens.Value.ToString())
}
if ($PSBoundParameters.ContainsKey("AiTimeoutSeconds")) {
    $CommandArgs += @("--ai-timeout-seconds", $AiTimeoutSeconds.Value.ToString([System.Globalization.CultureInfo]::InvariantCulture))
}
if ($ProviderDebug.IsPresent) {
    $CommandArgs += "--provider-debug"
}

& $Python @CommandArgs
exit $LASTEXITCODE
