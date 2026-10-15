# Camada Controller: consulta do resumo de atividade de alertas do usuário.
# Recebe a requisição, chama o Service e devolve o JSON. Não tem regra de
# negócio nem acesso ao banco.

from fastapi import APIRouter, Depends

from usuario_service.dtos.atividade_response import AtividadeAlertaResponse
from usuario_service.services.atividade_service import AtividadeService, get_atividade_service

router = APIRouter(prefix="/usuarios", tags=["Atividade de alertas"])


@router.get("/{usuario_id}/atividade-alertas", response_model=AtividadeAlertaResponse)
def buscar_atividade(
    usuario_id: int,
    service: AtividadeService = Depends(get_atividade_service),
):
    return service.buscar(usuario_id)
