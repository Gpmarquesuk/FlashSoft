param(
  [Parameter(Mandatory=$true)][string]$Spec,
  [string]$Branch
)

# Branch default + sufixo timestamp para evitar colisão
if (-not $Branch) {
  $name = [IO.Path]::GetFileNameWithoutExtension($Spec) -replace "[^\w\-]","-"
  $Branch = "autobot/$name"
}
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$Branch = "$Branch-$ts"

# Defaults de resiliência
if (-not $env:REQUEST_TIMEOUT_SECONDS -or $env:REQUEST_TIMEOUT_SECONDS -eq "") { $env:REQUEST_TIMEOUT_SECONDS = "60" }
if (-not $env:MAX_RETRIES_PER_CALL -or $env:MAX_RETRIES_PER_CALL -eq "") { $env:MAX_RETRIES_PER_CALL = "2" }

# Runner AUTÔNOMO (orquestrador sentinela)
.\.venv\Scripts\python.exe .\run_orchestrated.py --spec $Spec --branch $Branch
