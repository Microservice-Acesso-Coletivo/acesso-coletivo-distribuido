# Consumidor genérico: uma thread que escuta UMA fila do RabbitMQ.
# Cuida do que é igual para qualquer fila: conectar, reconectar se o broker
# cair, entregar cada mensagem ao handler, tentar de novo se falhar e mandar
# para a fila morta (DLQ) quando não houver mais o que fazer.
# O handler (em consumers/) é quem sabe o que fazer com a mensagem.

import logging
import threading
import time
from collections.abc import Callable

import pika
from pydantic import ValidationError

from acesso_api.messaging.broker import declarar_exchanges, declarar_fila, parametros_conexao

# Usa o logger do Uvicorn para as mensagens aparecerem nos logs do serviço.
log = logging.getLogger("uvicorn.error")

TENTATIVAS = 3
ESPERA_ENTRE_TENTATIVAS_SEGUNDOS = 1  # dobra a cada tentativa: 1s, 2s
ESPERA_RECONEXAO_SEGUNDOS = 5

# O handler recebe a chave de roteamento e o corpo (bytes) da mensagem.
Handler = Callable[[str, bytes], None]


class Consumidor(threading.Thread):
    def __init__(self, fila: str, chaves: list[str], handler: Handler):
        super().__init__(name=f"consumidor-{fila}", daemon=True)
        self.fila = fila
        self.chaves = chaves
        self.handler = handler
        self._parar = threading.Event()
        self._conexao: pika.BlockingConnection | None = None

    def parar(self) -> None:
        self._parar.set()

    def run(self) -> None:
        # O serviço sobe mesmo com o broker fora do ar: a thread fica tentando
        # reconectar e o consumo começa sozinho quando o RabbitMQ voltar.
        while not self._parar.is_set():
            try:
                self._escutar()
            except (pika.exceptions.AMQPError, OSError) as erro:
                log.warning(
                    "[%s] broker indisponivel (%s). Nova tentativa em %ss.",
                    self.fila, type(erro).__name__, ESPERA_RECONEXAO_SEGUNDOS,
                )
                self._parar.wait(ESPERA_RECONEXAO_SEGUNDOS)

    def _escutar(self) -> None:
        self._conexao = pika.BlockingConnection(parametros_conexao())
        try:
            canal = self._conexao.channel()
            declarar_exchanges(canal)
            declarar_fila(canal, self.fila, self.chaves)
            # Uma mensagem por vez: o broker só manda a próxima depois do ack.
            # Com várias instâncias do serviço, isso reparte o trabalho entre elas.
            canal.basic_qos(prefetch_count=1)
            canal.basic_consume(queue=self.fila, on_message_callback=self._ao_receber)
            log.info("[%s] escutando as chaves %s", self.fila, self.chaves)

            while not self._parar.is_set():
                # Processa eventos por até 1s e volta, para o loop poder checar o pedido de parada.
                self._conexao.process_data_events(time_limit=1)
        finally:
            try:
                if self._conexao.is_open:
                    self._conexao.close()
            except Exception:
                pass

    def _ao_receber(self, canal, metodo, propriedades, corpo: bytes) -> None:
        try:
            self._processar(metodo.routing_key, corpo)
            canal.basic_ack(delivery_tag=metodo.delivery_tag)
        except Exception as erro:
            # requeue=False manda a mensagem para a fila morta, em vez de ela
            # voltar para o início da fila e travar o consumo em um loop infinito.
            log.error("[%s] mensagem enviada para a fila morta: %s", self.fila, erro)
            canal.basic_nack(delivery_tag=metodo.delivery_tag, requeue=False)

    def _processar(self, chave: str, corpo: bytes) -> None:
        for tentativa in range(1, TENTATIVAS + 1):
            try:
                self.handler(chave, corpo)
                return
            except ValidationError:
                # JSON que não bate com o DTO não melhora tentando de novo.
                raise
            except Exception as erro:
                if tentativa == TENTATIVAS:
                    raise
                espera = ESPERA_ENTRE_TENTATIVAS_SEGUNDOS * 2 ** (tentativa - 1)
                log.warning(
                    "[%s] falha (%s), tentativa %s de %s. Repetindo em %ss.",
                    self.fila, erro, tentativa, TENTATIVAS, espera,
                )
                # Esperas curtas (1s e 2s): bem abaixo do heartbeat do broker, então a
                # conexão não cai enquanto o Consumer espera. Com prefetch 1, o broker
                # também não manda outra mensagem antes do ack.
                time.sleep(espera)
