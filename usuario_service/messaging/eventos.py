# DTO do evento que o usuario_service consome do broker (contrato de mensagens).
# Só os campos que interessam aqui: campos extras do JSON são ignorados.
# Cada microsserviço tem a sua cópia do contrato, sem compartilhar código.

from datetime import datetime

from pydantic import BaseModel


class AlertaGeradoEvent(BaseModel):
    """Publicado pelo transporte_service quando um alerta é calculado."""

    evento_id: str
    ocorrido_em: datetime
    usuario_id: int
    parada_nome: str
    nivel: str
