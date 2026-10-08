# Camada Controller: rotas /api/paradas, a entrada HTTP para tudo de parada.
# Recebe a requisição (já validada pelo DTO), chama o Service e devolve o
# JSON com o status code adequado.

from fastapi import APIRouter, Depends, status

from acesso_api.dtos.request import ParadaRequest
from acesso_api.dtos.response import ParadaResponse
from acesso_api.services.parada_service import ParadaService, get_parada_service

router = APIRouter(prefix="/api/paradas", tags=["Paradas"])


@router.get("", response_model=list[ParadaResponse])
def listar_paradas(service: ParadaService = Depends(get_parada_service)):
    return service.listar()


@router.post("", response_model=ParadaResponse, status_code=status.HTTP_201_CREATED)
def criar_parada(
    dados: ParadaRequest,
    service: ParadaService = Depends(get_parada_service),
):
    return service.criar(dados)
