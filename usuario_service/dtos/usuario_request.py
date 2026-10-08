# Camada DTO (entrada): define o JSON exato que o cliente pode enviar.
# A validação dos campos é feita aqui pelo Pydantic; se algo estiver errado,
# o FastAPI responde 422 antes mesmo de chegar no Controller.

from pydantic import BaseModel, EmailStr, Field

from usuario_service.models.usuario import PreferenciaAlerta

TAMANHO_MINIMO_SENHA = 6


class UsuarioCreateRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=TAMANHO_MINIMO_SENHA, max_length=72)
    preferencia_alerta: PreferenciaAlerta = PreferenciaAlerta.AMBOS


class UsuarioUpdateRequest(BaseModel):
    """Dados do cadastro que podem ser alterados. A senha não é trocada por aqui."""

    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    preferencia_alerta: PreferenciaAlerta


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)
