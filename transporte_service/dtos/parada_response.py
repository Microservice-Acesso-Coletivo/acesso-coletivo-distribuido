# Camada DTO (saída): define o JSON exato que o serviço devolve.
# ParadaResponse é a parada em si; AlertaResponse é o aviso de proximidade
# já pronto para o app transformar em áudio e/ou vibração.

import enum

from pydantic import BaseModel, ConfigDict

from transporte_service.clients.usuario_dto import TipoAlerta


class NivelAlerta(str, enum.Enum):
    """O quão perto a pessoa está da parada."""

    LONGE = "LONGE"
    PROXIMO = "PROXIMO"
    DESEMBARQUE = "DESEMBARQUE"


class ParadaResponse(BaseModel):
    # from_attributes permite montar o DTO a partir do Model do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

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
