# Camada Controller: ponto de entrada HTTP do serviço.
# Recebe a requisição (já validada pelo DTO), chama o Service e devolve o
# JSON com o status code adequado. Não tem regra de negócio nem acesso ao banco.

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from transporte_service.dtos.parada_request import AlertaRequest, ParadaRequest
from transporte_service.dtos.parada_response import AlertaResponse, ParadaResponse
from transporte_service.services.alerta_service import AlertaService, get_alerta_service
from transporte_service.services.parada_service import ParadaService, get_parada_service

router = APIRouter(prefix="/paradas", tags=["Paradas"])


@router.post("", response_model=ParadaResponse, status_code=status.HTTP_201_CREATED)
def criar_parada(
    dados: ParadaRequest,
    service: ParadaService = Depends(get_parada_service),
):
    return service.criar(dados)


@router.get("", response_model=list[ParadaResponse])
def listar_paradas(service: ParadaService = Depends(get_parada_service)):
    return service.listar()


# Esta rota precisa vir antes de /{parada_id}. Se viesse depois, o FastAPI
# tentaria ler "alerta" como um id numérico e responderia 422.
@router.get("/alerta", response_model=AlertaResponse)
def gerar_alerta(
    dados: Annotated[AlertaRequest, Query()],
    service: AlertaService = Depends(get_alerta_service),
):
    return service.gerar_alerta(dados)


@router.get("/{parada_id}", response_model=ParadaResponse)
def buscar_parada(
    parada_id: int,
    service: ParadaService = Depends(get_parada_service),
):
    return service.buscar(parada_id)


@router.put("/{parada_id}", response_model=ParadaResponse)
def atualizar_parada(
    parada_id: int,
    dados: ParadaRequest,
    service: ParadaService = Depends(get_parada_service),
):
    return service.atualizar(parada_id, dados)


@router.delete("/{parada_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_parada(
    parada_id: int,
    service: ParadaService = Depends(get_parada_service),
):
    service.remover(parada_id)
