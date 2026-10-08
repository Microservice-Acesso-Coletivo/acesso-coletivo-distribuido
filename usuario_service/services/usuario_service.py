# Camada Service: onde ficam as regras de negócio de usuário.
# Recebe o DTO de entrada, valida as regras (email único, login), aciona o
# Repository e converte o Model em DTO de saída. O Model nunca sai daqui.

from fastapi import Depends
from sqlalchemy.orm import Session

from usuario_service.database import get_db
from usuario_service.dtos.usuario_request import (
    LoginRequest,
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
)
from usuario_service.dtos.usuario_response import LoginResponse, UsuarioResponse
from usuario_service.exceptions import (
    CredenciaisInvalidas,
    EmailJaCadastrado,
    UsuarioNaoEncontrado,
)
from usuario_service.models.usuario import Usuario
from usuario_service.repositories.usuario_repository import UsuarioRepository
from usuario_service.services.senha import gerar_hash_senha, senha_confere


class UsuarioService:
    def __init__(self, repository: UsuarioRepository):
        self.repository = repository

    def criar(self, dados: UsuarioCreateRequest) -> UsuarioResponse:
        email = self._normalizar_email(dados.email)
        self._garantir_email_livre(email)

        usuario = Usuario(
            nome=dados.nome,
            email=email,
            senha_hash=gerar_hash_senha(dados.senha),
            preferencia_alerta=dados.preferencia_alerta,
        )
        return self._para_response(self.repository.salvar(usuario))

    def buscar(self, usuario_id: int) -> UsuarioResponse:
        return self._para_response(self._buscar_ou_falhar(usuario_id))

    def listar(self) -> list[UsuarioResponse]:
        return [self._para_response(usuario) for usuario in self.repository.listar()]

    def atualizar(self, usuario_id: int, dados: UsuarioUpdateRequest) -> UsuarioResponse:
        usuario = self._buscar_ou_falhar(usuario_id)
        email = self._normalizar_email(dados.email)
        self._garantir_email_livre(email, id_do_dono=usuario.id)

        usuario.nome = dados.nome
        usuario.email = email
        usuario.preferencia_alerta = dados.preferencia_alerta
        return self._para_response(self.repository.salvar(usuario))

    def remover(self, usuario_id: int) -> None:
        usuario = self._buscar_ou_falhar(usuario_id)
        self.repository.remover(usuario)

    def login(self, dados: LoginRequest) -> LoginResponse:
        usuario = self.repository.buscar_por_email(self._normalizar_email(dados.email))

        # Mesmo erro para "email não existe" e "senha errada": assim quem tenta
        # invadir não descobre quais emails estão cadastrados.
        if usuario is None or not senha_confere(dados.senha, usuario.senha_hash):
            raise CredenciaisInvalidas()

        return LoginResponse(
            mensagem="Login realizado com sucesso.",
            usuario=self._para_response(usuario),
        )

    def _buscar_ou_falhar(self, usuario_id: int) -> Usuario:
        usuario = self.repository.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontrado(usuario_id)
        return usuario

    def _garantir_email_livre(self, email: str, id_do_dono: int | None = None) -> None:
        """Lança EmailJaCadastrado se o email pertence a outro usuário."""
        existente = self.repository.buscar_por_email(email)
        if existente is None:
            return
        # Na atualização, o próprio usuário pode manter o email que já é dele.
        if existente.id == id_do_dono:
            return
        raise EmailJaCadastrado(email)

    def _normalizar_email(self, email: str) -> str:
        # Evita que "Ana@x.com" e "ana@x.com" virem dois cadastros.
        return email.strip().lower()

    def _para_response(self, usuario: Usuario) -> UsuarioResponse:
        return UsuarioResponse.model_validate(usuario)


def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    """Monta o Service com seu Repository para o Controller usar via Depends."""
    return UsuarioService(UsuarioRepository(db))
