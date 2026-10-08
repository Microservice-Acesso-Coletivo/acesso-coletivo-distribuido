# Derruba os 3 servicos do Acesso Coletivo (Windows PowerShell 5.1).
# Uso:  .\stop-all.ps1
# Procura quem esta escutando em cada porta, entao funciona mesmo que o servico
# tenha sido iniciado na mao, fora do run-all.ps1.

$servicos = @(
    @{ Nome = 'acesso_api';         Porta = 8080 },
    @{ Nome = 'transporte_service'; Porta = 8082 },
    @{ Nome = 'usuario_service';    Porta = 8081 }
)

foreach ($servico in $servicos) {
    $nome = $servico.Nome
    $porta = $servico.Porta

    $conexao = Get-NetTCPConnection -LocalPort $porta -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $conexao) {
        Write-Host "$nome : nada rodando na porta $porta."
        continue
    }

    $processo = Get-Process -Id $conexao.OwningProcess
    # Protecao: so encerra se for mesmo um Python, para nao matar outro programa
    # que por acaso esteja usando a mesma porta.
    if ($processo.ProcessName -notlike 'python*') {
        Write-Host "$nome : a porta $porta esta com '$($processo.ProcessName)', que nao e Python. Nao mexi."
        continue
    }

    Stop-Process -Id $processo.Id -Force -Confirm:$false
    Write-Host "$nome : encerrado (porta $porta, processo $($processo.Id))."
}
