# Exceções de domínio do transporte_service e o handler central.
# O Service (ou o Client) lança a exceção; o handler transforma em uma
# resposta JSON padronizada, no mesmo formato do usuario_service.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErroDeDominio(Exception):
    """Erro de regra de negócio. Cada filha define seu status HTTP e código."""

    status_code = 400
    codigo = "ERRO_DE_DOMINIO"

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ParadaNaoEncontrada(ErroDeDominio):
    status_code = 404
    codigo = "PARADA_NAO_ENCONTRADA"

    def __init__(self, parada_id: int):
        super().__init__(f"Parada com id {parada_id} não encontrada.")


class NenhumaParadaCadastrada(ErroDeDominio):
    status_code = 404
    codigo = "NENHUMA_PARADA_CADASTRADA"

    def __init__(self):
        super().__init__("Não há paradas cadastradas para calcular o alerta.")


class UsuarioNaoEncontrado(ErroDeDominio):
    status_code = 404
    codigo = "USUARIO_NAO_ENCONTRADO"

    def __init__(self, usuario_id: int):
        super().__init__(f"Usuário com id {usuario_id} não encontrado.")


class UsuarioServiceIndisponivel(ErroDeDominio):
    # 503 = este serviço está de pé, mas depende de outro que não respondeu.
    status_code = 503
    codigo = "USUARIO_SERVICE_INDISPONIVEL"

    def __init__(self):
        super().__init__(
            "O serviço de usuários está fora do ar ou demorou para responder. "
            "Tente novamente em instantes."
        )


def tratar_erro_de_dominio(request: Request, erro: ErroDeDominio) -> JSONResponse:
    """Monta o corpo JSON padrão de erro: status, código e mensagem."""
    corpo = {
        "status": erro.status_code,
        "erro": erro.codigo,
        "mensagem": erro.mensagem,
    }
    return JSONResponse(status_code=erro.status_code, content=corpo)


def registrar_handlers(app: FastAPI) -> None:
    """Liga o handler central ao app. O 422 de validação fica no padrão do FastAPI."""
    app.add_exception_handler(ErroDeDominio, tratar_erro_de_dominio)
