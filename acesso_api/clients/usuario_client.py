# Client: isola as chamadas HTTP síncronas ao usuario_service.
# Cada método corresponde a um endpoint do outro serviço e devolve o JSON
# da resposta; o Service é quem converte em DTO.

import os

from acesso_api.clients.chamada_http import chamar_servico

# 127.0.0.1 em vez de "localhost": no Windows, "localhost" tenta primeiro o
# IPv6 (::1), onde o Uvicorn não escuta, e cada chamada perde 2 segundos.
URL_USUARIO_SERVICE = os.getenv("USUARIO_SERVICE_URL", "http://127.0.0.1:8081")
NOME_SERVICO = "usuários"


class UsuarioClient:
    def criar(self, dados: dict) -> dict:
        return chamar_servico(NOME_SERVICO, "POST", f"{URL_USUARIO_SERVICE}/usuarios", corpo=dados)

    def buscar(self, usuario_id: int) -> dict:
        return chamar_servico(NOME_SERVICO, "GET", f"{URL_USUARIO_SERVICE}/usuarios/{usuario_id}")

    def login(self, dados: dict) -> dict:
        return chamar_servico(NOME_SERVICO, "POST", f"{URL_USUARIO_SERVICE}/usuarios/login", corpo=dados)
