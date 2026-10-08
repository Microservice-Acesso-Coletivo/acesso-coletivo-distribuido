# Sobe os 3 servicos do Acesso Coletivo em background (Windows PowerShell 5.1).
# Uso:  .\run-all.ps1        Para derrubar:  .\stop-all.ps1
# Este arquivo nao tem acentos de proposito: o PowerShell 5.1 le .ps1 sem BOM como ANSI.

$raiz = $PSScriptRoot
$python = Join-Path $raiz '.venv\Scripts\python.exe'
$pastaLogs = Join-Path $raiz 'logs'
$segundosDeEspera = 30

# O usuario_service sobe primeiro porque os outros dois dependem dele.
$servicos = @(
    @{ Nome = 'usuario_service';    Porta = 8081 },
    @{ Nome = 'transporte_service'; Porta = 8082 },
    @{ Nome = 'acesso_api';         Porta = 8080 }
)

function Test-PortaEmUso($porta) {
    $conexao = Get-NetTCPConnection -LocalPort $porta -State Listen -ErrorAction SilentlyContinue
    return [bool]$conexao
}

if (-not (Test-Path $python)) {
    Write-Host "Nao encontrei $python"
    Write-Host "Crie o ambiente antes:  python -m venv .venv"
    Write-Host "E instale as dependencias:  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

New-Item -ItemType Directory -Force $pastaLogs | Out-Null

foreach ($servico in $servicos) {
    $nome = $servico.Nome
    $porta = $servico.Porta

    if (Test-PortaEmUso $porta) {
        Write-Host "$nome : a porta $porta ja esta em uso, nao subi de novo (rode .\stop-all.ps1 para reiniciar)."
        continue
    }

    # -WorkingDirectory importa: os bancos SQLite ficam em .\data, relativo a raiz do projeto.
    # O Uvicorn escreve os acessos na saida padrao (.log) e o restante na saida de erro (.err.log).
    Start-Process -FilePath $python `
        -ArgumentList '-m', 'uvicorn', "$nome.main:app", '--port', $porta `
        -WorkingDirectory $raiz `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $pastaLogs "$nome.log") `
        -RedirectStandardError (Join-Path $pastaLogs "$nome.err.log")
    Write-Host "$nome : iniciando na porta $porta..."
}

# Espera os servicos comecarem a aceitar conexoes antes de dizer que esta tudo pronto.
$limite = (Get-Date).AddSeconds($segundosDeEspera)
do {
    Start-Sleep -Milliseconds 500
    $pendentes = @($servicos | Where-Object { -not (Test-PortaEmUso $_.Porta) })
} while ($pendentes.Count -gt 0 -and (Get-Date) -lt $limite)

if ($pendentes.Count -gt 0) {
    foreach ($servico in $pendentes) {
        Write-Host "$($servico.Nome) NAO subiu. Veja o erro em logs\$($servico.Nome).err.log"
    }
    exit 1
}

Write-Host ""
Write-Host "Tudo no ar:"
foreach ($servico in $servicos) {
    Write-Host "  $($servico.Nome)  http://127.0.0.1:$($servico.Porta)/docs"
}
Write-Host "Logs em .\logs    Para derrubar: .\stop-all.ps1"
