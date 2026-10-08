# Camada Service: operações de parada da acesso_api.
# A regra de parada mora no transporte_service; aqui o Service converte o DTO
# de entrada, aciona o Client e converte a resposta em DTO de saída.

from acesso_api.clients.transporte_client import TransporteClient
from acesso_api.dtos.request import ParadaRequest
from acesso_api.dtos.response import ParadaResponse


class ParadaService:
    def __init__(self, client: TransporteClient):
        self.client = client

    def listar(self) -> list[ParadaResponse]:
        return [ParadaResponse.model_validate(parada) for parada in self.client.listar_paradas()]

    def criar(self, dados: ParadaRequest) -> ParadaResponse:
        resposta = self.client.criar_parada(dados.model_dump(mode="json"))
        return ParadaResponse.model_validate(resposta)


def get_parada_service() -> ParadaService:
    """Monta o Service com seu Client para o Controller usar via Depends."""
    return ParadaService(TransporteClient())
