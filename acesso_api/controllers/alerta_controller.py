# Camada Controller: rotas /api/alertas, a entrada HTTP do alerta de proximidade.
# Recebe a requisição (já validada pelo DTO), chama o Service e devolve o
# JSON com o status code adequado.

from fastapi import APIRouter, Depends, Query, status

from acesso_api.dtos.request import AlertaRequest
from acesso_api.dtos.response import AlertaResponse, HistoricoAlertaResponse
from acesso_api.services.alerta_service import AlertaService, get_alerta_service

router = APIRouter(prefix="/api/alertas", tags=["Alertas"])


# 201 porque cada alerta gerado cria um registro novo no histórico.
@router.post("", response_model=AlertaResponse, status_code=status.HTTP_201_CREATED)
def gerar_alerta(
    dados: AlertaRequest,
    service: AlertaService = Depends(get_alerta_service),
):
    return service.gerar_alerta(dados)


@router.get("/historico", response_model=list[HistoricoAlertaResponse])
def listar_historico(
    usuario_id: int = Query(gt=0),
    service: AlertaService = Depends(get_alerta_service),
):
    return service.listar_historico(usuario_id)
