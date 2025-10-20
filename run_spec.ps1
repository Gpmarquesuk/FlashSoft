param(
  [Parameter(Mandatory=$true)][string]$Spec,
  [string]$Branch
)
# Branch padrão amigável + sufixo timestamp para evitar colisão
if (-not $Branch) {
  $name = [IO.Path]::GetFileNameWithoutExtension($Spec) -replace "[^\w\-]","-"
  $Branch = "autobot/$name"
}
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$Branch = "$Branch-$ts"

# Defaults de resiliência (podem ser ajustados via .env)
$env:REQUEST_TIMEOUT_SECONDS = $env:REQUEST_TIMEOUT_SECONDS ?? "60"
$env:MAX_RETRIES_PER_CALL    = $env:MAX_RETRIES_PER_CALL    ?? "2"

# Runner AUTÔNOMO (orquestrador sentinela)
.\.venv\Scripts\python.exe .\run_orchestrated.py --spec $Spec --branch $Branch
