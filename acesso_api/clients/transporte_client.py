# Client: isola as chamadas HTTP síncronas ao transporte_service.
# Cada método corresponde a um endpoint do outro serviço e devolve o JSON
# da resposta; o Service é quem converte em DTO.

import os

from acesso_api.clients.chamada_http import chamar_servico

# 127.0.0.1 em vez de "localhost": no Windows, "localhost" tenta primeiro o
# IPv6 (::1), onde o Uvicorn não escuta, e cada chamada perde 2 segundos.
URL_TRANSPORTE_SERVICE = os.getenv("TRANSPORTE_SERVICE_URL", "http://127.0.0.1:8082")
NOME_SERVICO = "transporte"


class TransporteClient:
    def listar_paradas(self) -> list[dict]:
        return chamar_servico(NOME_SERVICO, "GET", f"{URL_TRANSPORTE_SERVICE}/paradas")

    def criar_parada(self, dados: dict) -> dict:
        return chamar_servico(NOME_SERVICO, "POST", f"{URL_TRANSPORTE_SERVICE}/paradas", corpo=dados)

    def gerar_alerta(self, dados: dict) -> dict:
        """Envia usuário e posição e recebe o alerta calculado na hora."""
        return chamar_servico(
            NOME_SERVICO, "GET", f"{URL_TRANSPORTE_SERVICE}/paradas/alerta", parametros=dados
        )
