# Camada Service: regra do alerta de proximidade, o coração do app.
# Busca o usuário no usuario_service (chamada síncrona), acha a parada mais
# próxima da posição informada e monta o aviso conforme a distância.

import math

from fastapi import Depends
from sqlalchemy.orm import Session

from transporte_service.clients.usuario_client import UsuarioClient
from transporte_service.database import get_db
from transporte_service.dtos.parada_request import AlertaRequest
from transporte_service.dtos.parada_response import AlertaResponse, NivelAlerta, ParadaResponse
from transporte_service.exceptions import NenhumaParadaCadastrada
from transporte_service.models.parada import Parada
from transporte_service.repositories.parada_repository import ParadaRepository

RAIO_DA_TERRA_METROS = 6_371_000

# Distância máxima (em metros) de cada nível, do mais perto para o mais longe.
# Acima do último limite o nível é LONGE. Para mudar a regra, basta mexer aqui.
LIMITES_DE_NIVEL = [
    (100, NivelAlerta.DESEMBARQUE),
    (300, NivelAlerta.PROXIMO),
]

MENSAGENS_POR_NIVEL = {
    NivelAlerta.DESEMBARQUE: "Sua parada, {parada}, está a {distancia} metros. Prepare-se para descer.",
    NivelAlerta.PROXIMO: "Você está se aproximando de {parada}, a {distancia} metros.",
    NivelAlerta.LONGE: "A parada mais próxima é {parada}, a {distancia} metros.",
}


def calcular_distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância entre dois pontos do mapa pela fórmula de Haversine."""
    # A Terra é curva, então não dá para usar Pitágoras direto em latitude e
    # longitude. Haversine calcula o comprimento do arco sobre a esfera.
    # As funções trigonométricas do Python trabalham em radianos, não em graus.
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    diferenca_lat = math.radians(lat2 - lat1)
    diferenca_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(diferenca_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(diferenca_lon / 2) ** 2
    )
    angulo_central = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return RAIO_DA_TERRA_METROS * angulo_central


def definir_nivel(distancia_metros: int) -> NivelAlerta:
    """Devolve o primeiro nível cujo limite cobre a distância."""
    for limite, nivel in LIMITES_DE_NIVEL:
        if distancia_metros <= limite:
            return nivel
    return NivelAlerta.LONGE


class AlertaService:
    def __init__(self, repository: ParadaRepository, usuario_client: UsuarioClient):
        self.repository = repository
        self.usuario_client = usuario_client

    def gerar_alerta(self, dados: AlertaRequest) -> AlertaResponse:
        # O usuário vem primeiro: se ele não existir ou o usuario_service
        # estiver fora do ar, nem vale a pena consultar o banco.
        usuario = self.usuario_client.buscar_usuario(dados.usuario_id)
        parada, distancia = self._parada_mais_proxima(dados.latitude, dados.longitude)
        nivel = definir_nivel(distancia)

        return AlertaResponse(
            parada=ParadaResponse.model_validate(parada),
            distancia_metros=distancia,
            tipo_alerta=usuario.preferencia_alerta,
            nivel=nivel,
            mensagem=MENSAGENS_POR_NIVEL[nivel].format(parada=parada.nome, distancia=distancia),
        )

    def _parada_mais_proxima(self, latitude: float, longitude: float) -> tuple[Parada, int]:
        """Devolve a parada mais próxima e a distância até ela em metros inteiros."""
        paradas = self.repository.listar()
        if not paradas:
            raise NenhumaParadaCadastrada()

        def distancia_ate(parada: Parada) -> float:
            return calcular_distancia_metros(latitude, longitude, parada.latitude, parada.longitude)

        mais_proxima = min(paradas, key=distancia_ate)
        return mais_proxima, round(distancia_ate(mais_proxima))


def get_alerta_service(db: Session = Depends(get_db)) -> AlertaService:
    """Monta o Service com o Repository e o Client para o Controller usar via Depends."""
    return AlertaService(ParadaRepository(db), UsuarioClient())
