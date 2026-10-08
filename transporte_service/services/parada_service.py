# Camada Service: regras do cadastro de paradas.
# Recebe o DTO de entrada, aciona o Repository e converte o Model em DTO
# de saída. O Model nunca sai daqui.

from fastapi import Depends
from sqlalchemy.orm import Session

from transporte_service.database import get_db
from transporte_service.dtos.parada_request import ParadaRequest
from transporte_service.dtos.parada_response import ParadaResponse
from transporte_service.exceptions import ParadaNaoEncontrada
from transporte_service.models.parada import Parada
from transporte_service.repositories.parada_repository import ParadaRepository


class ParadaService:
    def __init__(self, repository: ParadaRepository):
        self.repository = repository

    def criar(self, dados: ParadaRequest) -> ParadaResponse:
        parada = Parada(**dados.model_dump())
        return self._para_response(self.repository.salvar(parada))

    def buscar(self, parada_id: int) -> ParadaResponse:
        return self._para_response(self._buscar_ou_falhar(parada_id))

    def listar(self) -> list[ParadaResponse]:
        return [self._para_response(parada) for parada in self.repository.listar()]

    def atualizar(self, parada_id: int, dados: ParadaRequest) -> ParadaResponse:
        parada = self._buscar_ou_falhar(parada_id)

        parada.nome = dados.nome
        parada.latitude = dados.latitude
        parada.longitude = dados.longitude
        parada.terminal = dados.terminal
        parada.linhas = dados.linhas
        return self._para_response(self.repository.salvar(parada))

    def remover(self, parada_id: int) -> None:
        parada = self._buscar_ou_falhar(parada_id)
        self.repository.remover(parada)

    def _buscar_ou_falhar(self, parada_id: int) -> Parada:
        parada = self.repository.buscar_por_id(parada_id)
        if parada is None:
            raise ParadaNaoEncontrada(parada_id)
        return parada

    def _para_response(self, parada: Parada) -> ParadaResponse:
        return ParadaResponse.model_validate(parada)


def get_parada_service(db: Session = Depends(get_db)) -> ParadaService:
    """Monta o Service com seu Repository para o Controller usar via Depends."""
    return ParadaService(ParadaRepository(db))
