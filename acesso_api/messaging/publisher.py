# Publisher: envia eventos para a exchange do broker.
# O Service só entrega o evento e a chave de roteamento. Quem vai receber
# (um, vários ou nenhum consumidor) é problema do broker, não do produtor.

import pika
from pydantic import BaseModel

from acesso_api.exceptions import BrokerIndisponivel
from acesso_api.messaging.broker import EXCHANGE_EVENTOS, declarar_exchanges, parametros_conexao


class EventoPublisher:
    def publicar(self, chave: str, evento: BaseModel) -> None:
        """Serializa o evento em JSON e publica. Só volta quando o broker confirmar."""
        # Uma conexão por publicação é simples e segura entre threads. Em produção
        # se reaproveitaria a conexão; para o trabalho, a simplicidade vale mais.
        try:
            conexao = pika.BlockingConnection(parametros_conexao())
            try:
                canal = conexao.channel()
                declarar_exchanges(canal)
                # Confirmação do broker: se ele não aceitar a mensagem, vira erro aqui
                # em vez de a API responder 202 sem que nada tenha sido enfileirado.
                canal.confirm_delivery()
                canal.basic_publish(
                    exchange=EXCHANGE_EVENTOS,
                    routing_key=chave,
                    body=evento.model_dump_json().encode("utf-8"),
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        # delivery_mode 2 = grava em disco: a mensagem sobrevive a um restart do broker.
                        delivery_mode=pika.DeliveryMode.Persistent,
                        message_id=getattr(evento, "evento_id", None),
                    ),
                )
            finally:
                if conexao.is_open:
                    conexao.close()
        except (pika.exceptions.AMQPError, OSError):
            # Único try/except do Publisher: erro de rede ou do broker vira exceção de domínio.
            raise BrokerIndisponivel()
