# Camada Controller: ponto de entrada HTTP do serviço.
# Recebe a requisição (já validada pelo DTO), chama o Service e devolve o
# JSON com o status code adequado. Não tem regra de negócio nem acesso ao banco.

from fastapi import APIRouter, Depends, status

from usuario_service.dtos.usuario_request import (
    LoginRequest,
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
)
from usuario_service.dtos.usuario_response import LoginResponse, UsuarioResponse
from usuario_service.services.usuario_service import UsuarioService, get_usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


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


@router.get("", response_model=list[UsuarioResponse])
def listar_usuarios(service: UsuarioService = Depends(get_usuario_service)):
    return service.listar()


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def buscar_usuario(
    usuario_id: int,
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.buscar(usuario_id)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdateRequest,
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.atualizar(usuario_id, dados)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_usuario(
    usuario_id: int,
    service: UsuarioService = Depends(get_usuario_service),
):
    service.remover(usuario_id)
