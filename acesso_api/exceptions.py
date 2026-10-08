# Exceções da acesso_api e os handlers centrais.
# A API quase não tem erro próprio: ou o serviço de destino não respondeu
# (503), ou ele respondeu um erro e a API repassa esse erro como veio.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErroDeDominio(Exception):
    """Erro de regra de negócio. Cada filha define seu status HTTP e código."""

    status_code = 400
    codigo = "ERRO_DE_DOMINIO"

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ServicoIndisponivel(ErroDeDominio):
    # 503 = a API está de pé, mas depende de um serviço que não respondeu.
    status_code = 503
    codigo = "SERVICO_INDISPONIVEL"

    def __init__(self, nome_servico: str):
        super().__init__(
            f"O serviço de {nome_servico} está fora do ar ou demorou para responder. "
            "Tente novamente em instantes."
        )


class ErroRepassado(Exception):
    """Erro que o serviço de destino devolveu (ex: 404, 409). Guarda status e corpo originais."""

    def __init__(self, status_code: int, corpo: dict):
        super().__init__(f"Serviço de destino respondeu {status_code}.")
        self.status_code = status_code
        self.corpo = corpo


def tratar_erro_de_dominio(request: Request, erro: ErroDeDominio) -> JSONResponse:
    """Monta o corpo JSON padrão de erro: status, código e mensagem."""
    corpo = {
        "status": erro.status_code,
        "erro": erro.codigo,
        "mensagem": erro.mensagem,
    }
    return JSONResponse(status_code=erro.status_code, content=corpo)


def tratar_erro_repassado(request: Request, erro: ErroRepassado) -> JSONResponse:
    """Devolve ao cliente o mesmo status e o mesmo JSON que o serviço de destino devolveu."""
    return JSONResponse(status_code=erro.status_code, content=erro.corpo)


def registrar_handlers(app: FastAPI) -> None:
    """Liga os handlers centrais ao app. O 422 de validação fica no padrão do FastAPI."""
    app.add_exception_handler(ErroDeDominio, tratar_erro_de_dominio)
    app.add_exception_handler(ErroRepassado, tratar_erro_repassado)
