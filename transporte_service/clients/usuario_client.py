# Client: isola a chamada HTTP síncrona ao usuario_service.
# O resto do serviço não sabe que existe httpx: pede um usuário e recebe
# um DTO ou uma exceção de domínio.

import os

import httpx

from transporte_service.clients.usuario_dto import UsuarioExterno
from transporte_service.exceptions import UsuarioNaoEncontrado, UsuarioServiceIndisponivel

# 127.0.0.1 em vez de "localhost": no Windows, "localhost" tenta primeiro o
# IPv6 (::1), onde o Uvicorn não escuta, e cada chamada perdia 2 segundos.
URL_USUARIO_SERVICE = os.getenv("USUARIO_SERVICE_URL", "http://127.0.0.1:8081")
# Sem timeout, um usuario_service travado deixaria este serviço travado também.
TIMEOUT_SEGUNDOS = 2.0


class UsuarioClient:
    def buscar_usuario(self, usuario_id: int) -> UsuarioExterno:
        """Busca o usuário no usuario_service e espera a resposta (síncrono)."""
        url = f"{URL_USUARIO_SERVICE}/usuarios/{usuario_id}"

        # Único try/except do serviço: é aqui que um erro de rede (conexão
        # recusada, timeout) vira uma exceção de domínio, tratada no handler central.
        try:
            resposta = httpx.get(url, timeout=TIMEOUT_SEGUNDOS)
        except httpx.RequestError:
            raise UsuarioServiceIndisponivel()

        if resposta.status_code == httpx.codes.NOT_FOUND:
            raise UsuarioNaoEncontrado(usuario_id)
        # Qualquer outra resposta que não seja 200 (ex: erro 500 do outro lado)
        # também significa que não dá para contar com o serviço agora.
        if resposta.status_code != httpx.codes.OK:
            raise UsuarioServiceIndisponivel()

        return UsuarioExterno.model_validate(resposta.json())
