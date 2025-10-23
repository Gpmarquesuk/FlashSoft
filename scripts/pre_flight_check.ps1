param(
  [Parameter(Mandatory = $true)][string]$BaseBranchPrefix,
  [string]$SpecName
)

function Write-Notice($message) {
  Write-Host "[factory] $message"
}

$ghPaths = @(
  (Get-Command gh -ErrorAction SilentlyContinue),
  (Get-Command 'C:\Program Files\GitHub CLI\gh.exe' -ErrorAction SilentlyContinue)
) | Where-Object { $_ -ne $null }

if (-not $ghPaths -or $ghPaths.Count -eq 0) {
  Write-Notice "gh CLI não encontrado; pulando pré-flight."
  return
}
$ghExe = $ghPaths[0].Source

try {
  $prJson = & $ghExe pr list --state open --json number,headRefName,createdAt,title --limit 100 2>$null
} catch {
  Write-Notice "Falha ao listar PRs: $($_.Exception.Message)"
  return
}

if (-not $prJson -or $prJson.Trim().Length -eq 0) { return }

try {
  $openPRs = $prJson | ConvertFrom-Json
} catch {
  Write-Notice "Não foi possível interpretar JSON retornado pelo gh."
  return
}

$matched = @()
foreach ($pr in $openPRs) {
  if ($pr.headRefName -like "$BaseBranchPrefix*") {
    $matched += $pr
  }
}

if (-not $matched -or $matched.Count -eq 0) { return }

Write-Notice "Encontrados $($matched.Count) PR(s) ativos com prefixo '$BaseBranchPrefix'. Iniciando arquivamento..."

foreach ($pr in $matched) {
  $branchName = $pr.headRefName
  $prNumber = $pr.number
  $reason = "automação detectou branch anterior ($branchName) para spec $SpecName"

  Write-Notice "Arquivando PR #$prNumber (branch $branchName) - $reason"

  $comment = @"
🚧 **FlashSoft Factory Auto-Closure**

Este PR foi fechado automaticamente porque o branch **$branchName** está obsoleto ($reason).

- Data/Hora: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- A fábrica abrirá um novo branch/PR para o mesmo spec.

*Mensagem gerada automaticamente pela FlashSoft.*
"@
  try {
    & $ghExe pr comment $prNumber --body $comment 2>$null
  } catch {
    Write-Notice "Não foi possível comentar no PR #$prNumber"
  }

  try {
    & $ghExe pr close $prNumber 2>$null
  } catch {
    Write-Notice "Falha ao fechar PR #$prNumber"
  }

  try {
    git push origin --delete $branchName 2>$null
    Write-Notice "Branch remoto $branchName removido."
  } catch {
    Write-Notice "Falha ao remover branch remoto $branchName."
  }

  try { git branch -D $branchName 2>$null } catch { }
}
