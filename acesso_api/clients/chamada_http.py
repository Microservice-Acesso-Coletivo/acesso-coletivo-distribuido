# Client (apoio): a chamada HTTP síncrona que os dois Clients usam.
# Fica em um só lugar para o tratamento de erro ser igual nos dois: serviço
# fora do ar vira 503 e erro devolvido pelo serviço é repassado como veio.

import httpx

from acesso_api.exceptions import ErroRepassado, ServicoIndisponivel

# Maior que os 2s que o transporte_service espera pelo usuario_service. Se
# fosse igual, a API desistiria antes de o transporte conseguir explicar o erro.
TIMEOUT_SEGUNDOS = 5.0


def chamar_servico(
    nome_servico: str,
    metodo: str,
    url: str,
    corpo: dict | None = None,
    parametros: dict | None = None,
):
    """Chama o serviço, espera a resposta e devolve o JSON já convertido."""
    # Único try/except da API: é aqui que um erro de rede (conexão recusada,
    # timeout) vira uma exceção de domínio, tratada no handler central.
    try:
        resposta = httpx.request(metodo, url, json=corpo, params=parametros, timeout=TIMEOUT_SEGUNDOS)
    except httpx.RequestError:
        raise ServicoIndisponivel(nome_servico)

    if resposta.is_success:
        return resposta.json()

    # 4xx é erro de quem pediu (404, 409, 401, 422): o cliente precisa saber
    # exatamente qual foi. O 503 também é repassado porque o serviço já explicou
    # no corpo qual dependência dele caiu.
    if resposta.is_client_error or resposta.status_code == httpx.codes.SERVICE_UNAVAILABLE:
        raise ErroRepassado(resposta.status_code, resposta.json())

    # Sobrou erro interno do serviço (5xx): para o cliente, ele está indisponível.
    raise ServicoIndisponivel(nome_servico)
