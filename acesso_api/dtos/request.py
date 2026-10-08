# Camada DTO (entrada): define o JSON exato que o cliente pode enviar à API.
# A validação é feita aqui pelo Pydantic; um pedido inválido recebe 422 e
# nem chega a ser repassado aos microsserviços.

from pydantic import BaseModel, EmailStr, Field

from acesso_api.models.historico_alerta import TipoAlerta

TAMANHO_MINIMO_SENHA = 6


class UsuarioCreateRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=TAMANHO_MINIMO_SENHA, max_length=72)
    preferencia_alerta: TipoAlerta = TipoAlerta.AMBOS


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)


class ParadaRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    terminal: bool = False
    linhas: str = Field(default="", max_length=200)


class AlertaRequest(BaseModel):
    """Quem é o usuário e onde ele está agora."""

    usuario_id: int = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
