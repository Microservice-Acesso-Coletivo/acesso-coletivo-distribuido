# Camada DTO (saída): define o JSON exato que o serviço devolve.
# Repare que não existe campo de senha aqui: o hash nunca sai do serviço.

from pydantic import BaseModel, ConfigDict

from usuario_service.models.usuario import PreferenciaAlerta


class UsuarioResponse(BaseModel):
    # from_attributes permite montar o DTO a partir do Model do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    preferencia_alerta: PreferenciaAlerta


class LoginResponse(BaseModel):
    mensagem: str
    usuario: UsuarioResponse
