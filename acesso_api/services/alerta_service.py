# Camada Service: fluxo principal da acesso_api.
# Pede o alerta ao transporte_service em tempo real, grava o resultado no
# histórico (banco próprio da API) e devolve o alerta ao cliente.

from fastapi import Depends
from sqlalchemy.orm import Session

from acesso_api.clients.transporte_client import TransporteClient
from acesso_api.database import get_db
from acesso_api.dtos.request import AlertaRequest
from acesso_api.dtos.response import AlertaResponse, HistoricoAlertaResponse
from acesso_api.models.historico_alerta import HistoricoAlerta
from acesso_api.repositories.historico_repository import HistoricoRepository


class AlertaService:
    def __init__(self, repository: HistoricoRepository, transporte_client: TransporteClient):
        self.repository = repository
        self.transporte_client = transporte_client

    def gerar_alerta(self, dados: AlertaRequest) -> AlertaResponse:
        # Se o transporte_service falhar, a exceção sai daqui e nada é gravado:
        # o histórico só guarda alertas que realmente foram entregues.
        resposta = self.transporte_client.gerar_alerta(dados.model_dump())
        alerta = AlertaResponse.model_validate(resposta)

        self.repository.salvar(self._montar_historico(dados, alerta))
        return alerta

    def listar_historico(self, usuario_id: int) -> list[HistoricoAlertaResponse]:
        historicos = self.repository.listar_por_usuario(usuario_id)
        return [HistoricoAlertaResponse.model_validate(historico) for historico in historicos]

    def _montar_historico(self, dados: AlertaRequest, alerta: AlertaResponse) -> HistoricoAlerta:
        return HistoricoAlerta(
            usuario_id=dados.usuario_id,
            latitude=dados.latitude,
            longitude=dados.longitude,
            parada_nome=alerta.parada.nome,
            distancia_metros=alerta.distancia_metros,
            nivel=alerta.nivel,
            tipo_alerta=alerta.tipo_alerta,
        )


def get_alerta_service(db: Session = Depends(get_db)) -> AlertaService:
    """Monta o Service com o Repository e o Client para o Controller usar via Depends."""
    return AlertaService(HistoricoRepository(db), TransporteClient())
