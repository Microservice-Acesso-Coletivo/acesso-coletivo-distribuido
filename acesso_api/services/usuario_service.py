# Camada Service: operações de usuário da acesso_api.
# A regra de usuário mora no usuario_service; aqui o Service converte o DTO
# de entrada, aciona o Client e converte a resposta em DTO de saída.

from acesso_api.clients.usuario_client import UsuarioClient
from acesso_api.dtos.request import LoginRequest, UsuarioCreateRequest
from acesso_api.dtos.response import LoginResponse, UsuarioResponse


class UsuarioService:
    def __init__(self, client: UsuarioClient):
        self.client = client

    def criar(self, dados: UsuarioCreateRequest) -> UsuarioResponse:
        # mode="json" transforma o enum em texto, pronto para ir no corpo da chamada.
        resposta = self.client.criar(dados.model_dump(mode="json"))
        return UsuarioResponse.model_validate(resposta)

    def buscar(self, usuario_id: int) -> UsuarioResponse:
        return UsuarioResponse.model_validate(self.client.buscar(usuario_id))

    def login(self, dados: LoginRequest) -> LoginResponse:
        resposta = self.client.login(dados.model_dump(mode="json"))
        return LoginResponse.model_validate(resposta)


def get_usuario_service() -> UsuarioService:
    """Monta o Service com seu Client para o Controller usar via Depends."""
    return UsuarioService(UsuarioClient())
