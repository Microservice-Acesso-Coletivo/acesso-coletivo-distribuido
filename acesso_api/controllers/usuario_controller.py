# Camada Controller: rotas /api/usuarios, a entrada HTTP para tudo de usuário.
# Recebe a requisição (já validada pelo DTO), chama o Service e devolve o
# JSON com o status code adequado.

from fastapi import APIRouter, Depends, status

from acesso_api.dtos.request import LoginRequest, UsuarioCreateRequest
from acesso_api.dtos.response import LoginResponse, UsuarioResponse
from acesso_api.services.usuario_service import UsuarioService, get_usuario_service

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: UsuarioCreateRequest,
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.criar(dados)


@router.post("/login", response_model=LoginResponse)
def fazer_login(
    dados: LoginRequest,
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.login(dados)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def buscar_usuario(
    usuario_id: int,
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.buscar(usuario_id)
