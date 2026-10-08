# Camada DTO (saída): define o JSON exato que a API devolve ao cliente.
# Os Services montam estes DTOs a partir do JSON dos microsserviços ou do
# Model do histórico. Nenhum deles tem campo de senha.

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from acesso_api.models.historico_alerta import NivelAlerta, TipoAlerta


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    preferencia_alerta: TipoAlerta


class LoginResponse(BaseModel):
    mensagem: str
    usuario: UsuarioResponse


class ParadaResponse(BaseModel):
    id: int
    nome: str
    latitude: float
    longitude: float
    terminal: bool
    linhas: str


class AlertaResponse(BaseModel):
    parada: ParadaResponse
    distancia_metros: int
    tipo_alerta: TipoAlerta
    nivel: NivelAlerta
    mensagem: str


class HistoricoAlertaResponse(BaseModel):
    # from_attributes permite montar o DTO a partir do Model do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    latitude: float
    longitude: float
    parada_nome: str
    distancia_metros: int
    nivel: NivelAlerta
    tipo_alerta: TipoAlerta
    criado_em: datetime
