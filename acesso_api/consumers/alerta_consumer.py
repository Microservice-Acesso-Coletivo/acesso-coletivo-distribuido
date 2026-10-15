# Consumer da acesso_api: escuta a fila "acesso.alerta-concluido".
# Recebe o resultado do cálculo (alerta.gerado ou alerta.falhou), desserializa
# a mensagem para o DTO do evento e aciona o Service. Não tem regra de
# negócio: só traduz "mensagem do broker" em "chamada ao Service".

import logging

from acesso_api.database import SessionLocal
from acesso_api.messaging.broker import CHAVE_ALERTA_FALHOU, CHAVE_ALERTA_GERADO
from acesso_api.messaging.consumidor import Consumidor
from acesso_api.messaging.eventos import AlertaFalhouEvent, AlertaGeradoEvent
from acesso_api.services.alerta_service import criar_alerta_service

log = logging.getLogger("uvicorn.error")

FILA = "acesso.alerta-concluido"
CHAVES = [CHAVE_ALERTA_GERADO, CHAVE_ALERTA_FALHOU]


def tratar_mensagem(chave: str, corpo: bytes) -> None:
    # Fora de uma requisição HTTP não existe Depends: o Consumer abre a sua
    # própria sessão do banco e a fecha ao terminar cada mensagem.
    if chave == CHAVE_ALERTA_GERADO:
        evento = AlertaGeradoEvent.model_validate_json(corpo)
        with SessionLocal() as db:
            criar_alerta_service(db).registrar_alerta_gerado(evento)
        log.info("[acesso_api] alerta gerado registrado (solicitacao %s)", evento.solicitacao_id)
    elif chave == CHAVE_ALERTA_FALHOU:
        evento = AlertaFalhouEvent.model_validate_json(corpo)
        with SessionLocal() as db:
            criar_alerta_service(db).registrar_alerta_falhou(evento)
        log.info("[acesso_api] falha registrada (solicitacao %s): %s", evento.solicitacao_id, evento.codigo)
    else:
        log.warning("[acesso_api] chave desconhecida ignorada: %s", chave)


def criar_consumidor() -> Consumidor:
    return Consumidor(FILA, CHAVES, tratar_mensagem)
