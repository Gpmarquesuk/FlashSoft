param(
  [Parameter(Mandatory = $true)][string]$Spec,
  [string]$Branch
)

function Ensure-GitHubEnv {
  param(
    [string]$TokenVar = "GITHUB_TOKEN",
    [string]$RepoVar = "GITHUB_REPO_FULL"
  )

  $tokenValue = $null
  if (Test-Path env:$TokenVar) {
    $tokenValue = (Get-Item env:$TokenVar).Value
  }
  if (-not $tokenValue) {
    try {
      $token = (& 'C:\Program Files\GitHub CLI\gh.exe' auth token 2>$null).Trim()
      if ($token) {
        Set-Item -Path env:$TokenVar -Value $token
      }
    } catch {}
  }

  $repoValue = $null
  if (Test-Path env:$RepoVar) {
    $repoValue = (Get-Item env:$RepoVar).Value
  }
  if (-not $repoValue) {
    try {
      $remoteUrl = git remote get-url origin 2>$null
      if ($remoteUrl -match "github.com[:/](.+?)(\.git)?$") {
        Set-Item -Path env:$RepoVar -Value $Matches[1]
      }
    } catch {}
  }
}

Ensure-GitHubEnv

$specName = [IO.Path]::GetFileNameWithoutExtension($Spec) -replace "[^\w\-]", "-"
$baseBranchPrefix = if ($Branch) { $Branch } else { "autobot/$specName" }

$preFlight = Join-Path -Path (Get-Location) -ChildPath "scripts\pre_flight_check.ps1"
if (Test-Path $preFlight) {
  try { & $preFlight -BaseBranchPrefix $baseBranchPrefix -SpecName $specName } catch {}
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Branch = "$baseBranchPrefix-$timestamp"

if (-not $env:REQUEST_TIMEOUT_SECONDS -or $env:REQUEST_TIMEOUT_SECONDS -eq "") { $env:REQUEST_TIMEOUT_SECONDS = "60" }
if (-not $env:MAX_RETRIES_PER_CALL -or $env:MAX_RETRIES_PER_CALL -eq "") { $env:MAX_RETRIES_PER_CALL = "2" }

.\.venv\Scripts\python.exe .\run_orchestrated.py --spec $Spec --branch $Branch
