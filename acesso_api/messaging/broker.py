# Configuração do RabbitMQ usada pela acesso_api (Publisher e Consumer).
# Concentra o endereço do broker, os nomes da exchange e das chaves de
# roteamento, e a criação (idempotente) da topologia: declarar duas vezes a
# mesma exchange ou fila com os mesmos argumentos não causa erro.

import os

import pika

# 127.0.0.1 em vez de "localhost" pelo mesmo motivo das chamadas HTTP: no
# Windows, "localhost" tenta primeiro o IPv6 e perde tempo.
URL_BROKER = os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/%2F")

# Exchange do tipo "topic": quem publica só informa a chave de roteamento
# (ex: "alerta.gerado") e o broker entrega para toda fila cujo padrão combine.
EXCHANGE_EVENTOS = "acesso.eventos"
# Exchange das mensagens mortas (DLX): para onde vai uma mensagem que não deu
# para processar. Cada fila tem a sua fila morta (.dlq) ligada aqui.
EXCHANGE_MORTAS = "acesso.eventos.dlx"

CHAVE_ALERTA_SOLICITADO = "alerta.solicitado"
CHAVE_ALERTA_GERADO = "alerta.gerado"
CHAVE_ALERTA_FALHOU = "alerta.falhou"


def parametros_conexao() -> pika.URLParameters:
    parametros = pika.URLParameters(URL_BROKER)
    # Sem estes limites, um broker fora do ar seguraria a requisição por muito tempo.
    parametros.socket_timeout = 3.0
    parametros.connection_attempts = 1
    return parametros


def declarar_exchanges(canal) -> None:
    canal.exchange_declare(exchange=EXCHANGE_EVENTOS, exchange_type="topic", durable=True)
    canal.exchange_declare(exchange=EXCHANGE_MORTAS, exchange_type="direct", durable=True)


def declarar_fila(canal, fila: str, chaves: list[str]) -> None:
    """Cria a fila durável (com sua fila morta) e liga às chaves de roteamento."""
    # A fila morta recebe o que for rejeitado da fila principal.
    canal.queue_declare(queue=f"{fila}.dlq", durable=True)
    canal.queue_bind(queue=f"{fila}.dlq", exchange=EXCHANGE_MORTAS, routing_key=fila)

    canal.queue_declare(
        queue=fila,
        durable=True,
        arguments={
            "x-dead-letter-exchange": EXCHANGE_MORTAS,
            "x-dead-letter-routing-key": fila,
        },
    )
    for chave in chaves:
        canal.queue_bind(queue=fila, exchange=EXCHANGE_EVENTOS, routing_key=chave)
