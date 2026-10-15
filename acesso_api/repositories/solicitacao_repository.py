# Camada Repository: única parte da acesso_api que fala com o banco.
# Grava e consulta as solicitações de alerta. Não valida regra de negócio.

from sqlalchemy.orm import Session

from acesso_api.models.historico_alerta import HistoricoAlerta
from acesso_api.models.solicitacao_alerta import SolicitacaoAlerta


class SolicitacaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, solicitacao: SolicitacaoAlerta) -> SolicitacaoAlerta:
        self.db.add(solicitacao)
        self.db.commit()
        self.db.refresh(solicitacao)
        return solicitacao

    def buscar_por_id(self, solicitacao_id: int) -> SolicitacaoAlerta | None:
        return self.db.get(SolicitacaoAlerta, solicitacao_id)

    def concluir(self, solicitacao: SolicitacaoAlerta, historico: HistoricoAlerta) -> SolicitacaoAlerta:
        """Grava a solicitação concluída e o histórico no mesmo commit: ou vão os dois ou nenhum."""
        # Se o processo caísse entre dois commits, a mensagem seria reentregue e
        # o histórico ficaria duplicado.
        self.db.add(solicitacao)
        self.db.add(historico)
        self.db.commit()
        self.db.refresh(solicitacao)
        return solicitacao
