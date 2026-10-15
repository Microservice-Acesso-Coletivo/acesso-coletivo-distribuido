# Camada Service: regras do resumo de atividade de alertas.
# registrar_alerta é chamado pelo Consumer a cada evento "alerta.gerado";
# buscar atende o endpoint HTTP de consulta.

from fastapi import Depends
from sqlalchemy.orm import Session

from usuario_service.database import get_db
from usuario_service.dtos.atividade_response import AtividadeAlertaResponse
from usuario_service.exceptions import UsuarioNaoEncontrado
from usuario_service.messaging.eventos import AlertaGeradoEvent
from usuario_service.models.atividade_alerta import AtividadeAlerta
from usuario_service.repositories.atividade_repository import AtividadeRepository
from usuario_service.repositories.usuario_repository import UsuarioRepository


class AtividadeService:
    def __init__(self, repository: AtividadeRepository, usuario_repository: UsuarioRepository):
        self.repository = repository
        self.usuario_repository = usuario_repository

    def registrar_alerta(self, evento: AlertaGeradoEvent) -> None:
        atividade = self.repository.buscar_por_usuario(evento.usuario_id)
        if atividade is None:
            atividade = AtividadeAlerta(usuario_id=evento.usuario_id, total_alertas=0)
        elif atividade.ultimo_evento_id == evento.evento_id:
            # Mensagem repetida (o broker entrega "pelo menos uma vez"): não conta de novo.
            return

        atividade.total_alertas += 1
        atividade.ultima_parada = evento.parada_nome
        atividade.ultimo_nivel = evento.nivel
        atividade.ultimo_alerta_em = evento.ocorrido_em
        atividade.ultimo_evento_id = evento.evento_id
        self.repository.salvar(atividade)

    def buscar(self, usuario_id: int) -> AtividadeAlertaResponse:
        if self.usuario_repository.buscar_por_id(usuario_id) is None:
            raise UsuarioNaoEncontrado(usuario_id)

        atividade = self.repository.buscar_por_usuario(usuario_id)
        if atividade is None:
            # Usuário existe, mas ainda não recebeu nenhum alerta.
            return AtividadeAlertaResponse(usuario_id=usuario_id, total_alertas=0)
        return AtividadeAlertaResponse.model_validate(atividade)


def criar_atividade_service(db: Session) -> AtividadeService:
    """Monta o Service com seus Repositories. Usado pelo Controller e pelo Consumer."""
    return AtividadeService(AtividadeRepository(db), UsuarioRepository(db))


def get_atividade_service(db: Session = Depends(get_db)) -> AtividadeService:
    """Versão para o Controller usar via Depends."""
    return criar_atividade_service(db)
