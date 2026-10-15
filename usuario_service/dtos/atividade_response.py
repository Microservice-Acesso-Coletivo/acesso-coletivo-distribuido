# Camada DTO (saída): resumo de atividade de alertas do usuário.
# Os campos do último alerta vêm vazios para quem ainda não recebeu nenhum.

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AtividadeAlertaResponse(BaseModel):
    # from_attributes permite montar o DTO a partir do Model do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    usuario_id: int
    total_alertas: int
    ultima_parada: str | None = None
    ultimo_nivel: str | None = None
    ultimo_alerta_em: datetime | None = None
