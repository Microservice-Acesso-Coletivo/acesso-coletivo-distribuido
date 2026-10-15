# Consumer do usuario_service: escuta a fila "usuario.alerta-gerado".
# É o segundo assinante do evento "alerta.gerado" (o primeiro é a acesso_api,
# que grava o histórico). O transporte_service publica uma vez só e o broker
# entrega uma cópia para cada fila: isso é o padrão Publish/Subscribe.
# Aqui o evento atualiza o resumo de atividade de alertas do usuário.

import logging

from usuario_service.database import SessionLocal
from usuario_service.messaging.broker import CHAVE_ALERTA_GERADO
from usuario_service.messaging.consumidor import Consumidor
from usuario_service.messaging.eventos import AlertaGeradoEvent
from usuario_service.services.atividade_service import criar_atividade_service

log = logging.getLogger("uvicorn.error")

FILA = "usuario.alerta-gerado"
CHAVES = [CHAVE_ALERTA_GERADO]


def tratar_mensagem(chave: str, corpo: bytes) -> None:
    evento = AlertaGeradoEvent.model_validate_json(corpo)
    # Fora de uma requisição HTTP não existe Depends: o Consumer abre a sua
    # própria sessão do banco e a fecha ao terminar cada mensagem.
    with SessionLocal() as db:
        criar_atividade_service(db).registrar_alerta(evento)
    log.info("[usuario_service] atividade do usuario %s atualizada", evento.usuario_id)


def criar_consumidor() -> Consumidor:
    return Consumidor(FILA, CHAVES, tratar_mensagem)
