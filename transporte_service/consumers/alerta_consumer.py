# Consumer do transporte_service: escuta a fila "transporte.alerta-solicitado".
# Recebe o pedido de alerta publicado pela acesso_api, desserializa a mensagem
# para o DTO do evento e aciona a camada de Service para calcular o alerta.
#
# Padrão Point-to-Point: é uma fila só e cada mensagem vai para UMA instância.
# Se subirem duas instâncias do transporte_service, elas dividem o trabalho.

import logging

from transporte_service.database import SessionLocal
from transporte_service.messaging.broker import CHAVE_ALERTA_SOLICITADO
from transporte_service.messaging.consumidor import Consumidor
from transporte_service.messaging.eventos import AlertaSolicitadoEvent
from transporte_service.services.alerta_service import criar_alerta_service

log = logging.getLogger("uvicorn.error")

FILA = "transporte.alerta-solicitado"
CHAVES = [CHAVE_ALERTA_SOLICITADO]


def tratar_mensagem(chave: str, corpo: bytes) -> None:
    evento = AlertaSolicitadoEvent.model_validate_json(corpo)
    # Fora de uma requisição HTTP não existe Depends: o Consumer abre a sua
    # própria sessão do banco e a fecha ao terminar cada mensagem.
    with SessionLocal() as db:
        criar_alerta_service(db).processar_solicitacao(evento)
    log.info("[transporte_service] pedido %s processado", evento.solicitacao_id)


def criar_consumidor() -> Consumidor:
    return Consumidor(FILA, CHAVES, tratar_mensagem)
