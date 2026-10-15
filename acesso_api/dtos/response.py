# Camada DTO (saída): define o JSON exato que a API devolve ao cliente.
# Os Services montam estes DTOs a partir do JSON dos microsserviços ou dos
# Models (histórico e solicitação). Nenhum deles tem campo de senha.

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from acesso_api.models.historico_alerta import NivelAlerta, TipoAlerta
from acesso_api.models.solicitacao_alerta import StatusSolicitacao


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


class AlertaAceitoResponse(BaseModel):
    """Corpo do 202 Accepted: o pedido foi aceito, mas o alerta ainda não foi calculado."""

    solicitacao_id: int
    status: StatusSolicitacao
    mensagem: str
    # Rota onde o cliente consulta o andamento do pedido.
    consulta: str


class SolicitacaoAlertaResponse(BaseModel):
    """Andamento de um pedido de alerta. Os campos do resultado vêm vazios até concluir."""

    # from_attributes permite montar o DTO a partir do Model do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    status: StatusSolicitacao
    latitude: float
    longitude: float
    parada_nome: str | None = None
    distancia_metros: int | None = None
    nivel: NivelAlerta | None = None
    tipo_alerta: TipoAlerta | None = None
    mensagem: str | None = None
    codigo_erro: str | None = None
    motivo_falha: str | None = None
    criado_em: datetime
    atualizado_em: datetime


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
