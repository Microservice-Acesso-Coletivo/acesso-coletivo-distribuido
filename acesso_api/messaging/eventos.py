# DTOs dos eventos que trafegam pelo broker (contrato de mensagens).
# Um evento diz "o que aconteceu", no passado, e carrega só os dados
# necessários. Como nas chamadas HTTP, cada microsserviço tem a sua cópia
# do contrato: ninguém compartilha código, só o JSON.

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from acesso_api.models.historico_alerta import NivelAlerta, TipoAlerta


class EventoBase(BaseModel):
    # evento_id identifica a mensagem: quem recebe a mesma mensagem duas vezes
    # (o broker garante "pelo menos uma entrega") consegue perceber a repetição.
    evento_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ocorrido_em: datetime = Field(default_factory=datetime.now)


class AlertaSolicitadoEvent(EventoBase):
    """Publicado pela acesso_api: alguém pediu um alerta nesta posição."""

    solicitacao_id: int
    usuario_id: int
    latitude: float
    longitude: float


class AlertaGeradoEvent(EventoBase):
    """Consumido pela acesso_api: o alerta foi calculado."""

    solicitacao_id: int
    usuario_id: int
    parada_id: int
    parada_nome: str
    distancia_metros: int
    nivel: NivelAlerta
    tipo_alerta: TipoAlerta
    mensagem: str


class AlertaFalhouEvent(EventoBase):
    """Consumido pela acesso_api: o pedido não pôde ser atendido (erro de negócio)."""

    solicitacao_id: int
    usuario_id: int
    codigo: str
    motivo: str
