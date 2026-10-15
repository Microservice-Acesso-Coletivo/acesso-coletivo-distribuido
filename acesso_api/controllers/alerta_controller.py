# Camada Controller: rotas /api/alertas, a entrada HTTP do alerta de proximidade.
# Recebe a requisição (já validada pelo DTO), chama o Service e devolve o
# JSON com o status code adequado.

from fastapi import APIRouter, Depends, Query, status

from acesso_api.dtos.request import AlertaRequest
from acesso_api.dtos.response import (
    AlertaAceitoResponse,
    HistoricoAlertaResponse,
    SolicitacaoAlertaResponse,
)
from acesso_api.services.alerta_service import AlertaService, get_alerta_service

router = APIRouter(prefix="/api/alertas", tags=["Alertas"])


# 202 Accepted: o pedido foi aceito e entregue ao broker, mas o alerta ainda
# vai ser calculado em segundo plano. O cliente consulta o resultado depois.
@router.post("", response_model=AlertaAceitoResponse, status_code=status.HTTP_202_ACCEPTED)
def solicitar_alerta(
    dados: AlertaRequest,
    service: AlertaService = Depends(get_alerta_service),
):
    return service.solicitar_alerta(dados)


# Esta rota precisa vir antes de /{solicitacao_id}. Se viesse depois, o FastAPI
# tentaria ler "historico" como um id numérico e responderia 422.
@router.get("/historico", response_model=list[HistoricoAlertaResponse])
def listar_historico(
    usuario_id: int = Query(gt=0),
    service: AlertaService = Depends(get_alerta_service),
):
    return service.listar_historico(usuario_id)


@router.get("/{solicitacao_id}", response_model=SolicitacaoAlertaResponse)
def consultar_solicitacao(
    solicitacao_id: int,
    service: AlertaService = Depends(get_alerta_service),
):
    return service.consultar_solicitacao(solicitacao_id)
