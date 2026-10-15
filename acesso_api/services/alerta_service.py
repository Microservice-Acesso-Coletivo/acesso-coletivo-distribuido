# Camada Service: fluxo principal da acesso_api, agora assíncrono.
# Lado produtor: salva o pedido no banco da API, publica o evento
# AlertaSolicitadoEvent e responde na hora (202), sem esperar o cálculo.
# Lado consumidor: quando chega o resultado (alerta gerado ou falha), atualiza
# a solicitação e grava o histórico. A API não sabe quem calcula o alerta.

from fastapi import Depends
from sqlalchemy.orm import Session

from acesso_api.database import get_db
from acesso_api.dtos.request import AlertaRequest
from acesso_api.dtos.response import (
    AlertaAceitoResponse,
    HistoricoAlertaResponse,
    SolicitacaoAlertaResponse,
)
from acesso_api.exceptions import BrokerIndisponivel, SolicitacaoNaoEncontrada
from acesso_api.messaging.broker import CHAVE_ALERTA_SOLICITADO
from acesso_api.messaging.eventos import (
    AlertaFalhouEvent,
    AlertaGeradoEvent,
    AlertaSolicitadoEvent,
)
from acesso_api.messaging.publisher import EventoPublisher
from acesso_api.models.historico_alerta import HistoricoAlerta
from acesso_api.models.solicitacao_alerta import SolicitacaoAlerta, StatusSolicitacao
from acesso_api.repositories.historico_repository import HistoricoRepository
from acesso_api.repositories.solicitacao_repository import SolicitacaoRepository


class AlertaService:
    def __init__(
        self,
        historico_repository: HistoricoRepository,
        solicitacao_repository: SolicitacaoRepository,
        publisher: EventoPublisher,
    ):
        self.historico_repository = historico_repository
        self.solicitacao_repository = solicitacao_repository
        self.publisher = publisher

    # ---------- Produtor ----------

    def solicitar_alerta(self, dados: AlertaRequest) -> AlertaAceitoResponse:
        # 1) Lógica local: salva o pedido no banco da API (status PENDENTE).
        solicitacao = self.solicitacao_repository.salvar(
            SolicitacaoAlerta(
                usuario_id=dados.usuario_id,
                latitude=dados.latitude,
                longitude=dados.longitude,
            )
        )

        # 2) Serializa o evento e publica no broker. Não há nome de serviço
        #    aqui: só a chave de roteamento "alerta.solicitado".
        evento = AlertaSolicitadoEvent(
            solicitacao_id=solicitacao.id,
            usuario_id=dados.usuario_id,
            latitude=dados.latitude,
            longitude=dados.longitude,
        )
        try:
            self.publisher.publicar(CHAVE_ALERTA_SOLICITADO, evento)
        except BrokerIndisponivel:
            # O pedido já está no banco, mas nunca chegou à fila. Marca como falha
            # para não ficar PENDENTE para sempre e avisa o cliente (503).
            solicitacao.status = StatusSolicitacao.FALHOU
            solicitacao.codigo_erro = BrokerIndisponivel.codigo
            solicitacao.motivo_falha = "Não foi possível publicar o pedido no broker."
            self.solicitacao_repository.salvar(solicitacao)
            raise

        return AlertaAceitoResponse(
            solicitacao_id=solicitacao.id,
            status=solicitacao.status,
            mensagem="Pedido de alerta recebido. O cálculo é feito em segundo plano.",
            consulta=f"/api/alertas/{solicitacao.id}",
        )

    def consultar_solicitacao(self, solicitacao_id: int) -> SolicitacaoAlertaResponse:
        solicitacao = self.solicitacao_repository.buscar_por_id(solicitacao_id)
        if solicitacao is None:
            raise SolicitacaoNaoEncontrada(solicitacao_id)
        return SolicitacaoAlertaResponse.model_validate(solicitacao)

    def listar_historico(self, usuario_id: int) -> list[HistoricoAlertaResponse]:
        historicos = self.historico_repository.listar_por_usuario(usuario_id)
        return [HistoricoAlertaResponse.model_validate(historico) for historico in historicos]

    # ---------- Consumidor (chamado pelos Consumers) ----------

    def registrar_alerta_gerado(self, evento: AlertaGeradoEvent) -> None:
        solicitacao = self.solicitacao_repository.buscar_por_id(evento.solicitacao_id)
        # Solicitação desconhecida ou já resolvida: o broker entrega "pelo menos uma
        # vez", então a mesma mensagem pode chegar repetida. Ignorar torna o
        # processamento idempotente (processar duas vezes dá o mesmo resultado).
        if solicitacao is None or solicitacao.status != StatusSolicitacao.PENDENTE:
            return

        solicitacao.status = StatusSolicitacao.CONCLUIDA
        solicitacao.parada_nome = evento.parada_nome
        solicitacao.distancia_metros = evento.distancia_metros
        solicitacao.nivel = evento.nivel
        solicitacao.tipo_alerta = evento.tipo_alerta
        solicitacao.mensagem = evento.mensagem

        historico = HistoricoAlerta(
            usuario_id=solicitacao.usuario_id,
            latitude=solicitacao.latitude,
            longitude=solicitacao.longitude,
            parada_nome=evento.parada_nome,
            distancia_metros=evento.distancia_metros,
            nivel=evento.nivel,
            tipo_alerta=evento.tipo_alerta,
        )
        self.solicitacao_repository.concluir(solicitacao, historico)

    def registrar_alerta_falhou(self, evento: AlertaFalhouEvent) -> None:
        solicitacao = self.solicitacao_repository.buscar_por_id(evento.solicitacao_id)
        if solicitacao is None or solicitacao.status != StatusSolicitacao.PENDENTE:
            return

        # Como antes, o histórico só guarda alertas que realmente foram entregues.
        solicitacao.status = StatusSolicitacao.FALHOU
        solicitacao.codigo_erro = evento.codigo
        solicitacao.motivo_falha = evento.motivo
        self.solicitacao_repository.salvar(solicitacao)


def criar_alerta_service(db: Session) -> AlertaService:
    """Monta o Service com seus Repositories e o Publisher. Usado pelo Controller e pelo Consumer."""
    return AlertaService(HistoricoRepository(db), SolicitacaoRepository(db), EventoPublisher())


def get_alerta_service(db: Session = Depends(get_db)) -> AlertaService:
    """Versão para o Controller usar via Depends."""
    return criar_alerta_service(db)
