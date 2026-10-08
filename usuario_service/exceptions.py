# Exceções de domínio do usuario_service e o handler central.
# O Service lança a exceção; o handler transforma em uma resposta JSON
# padronizada com o status code certo. Assim não há try/except espalhado.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErroDeDominio(Exception):
    """Erro de regra de negócio. Cada filha define seu status HTTP e código."""

    status_code = 400
    codigo = "ERRO_DE_DOMINIO"

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class UsuarioNaoEncontrado(ErroDeDominio):
    status_code = 404
    codigo = "USUARIO_NAO_ENCONTRADO"

    def __init__(self, usuario_id: int):
        super().__init__(f"Usuário com id {usuario_id} não encontrado.")


class EmailJaCadastrado(ErroDeDominio):
    status_code = 409
    codigo = "EMAIL_JA_CADASTRADO"

    def __init__(self, email: str):
        super().__init__(f"O email {email} já está cadastrado.")


class CredenciaisInvalidas(ErroDeDominio):
    status_code = 401
    codigo = "CREDENCIAIS_INVALIDAS"

    def __init__(self):
        super().__init__("Email ou senha inválidos.")


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
