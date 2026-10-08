# Camada Repository: única parte da acesso_api que fala com o banco.
# Grava e consulta o histórico de alertas. Não valida regra de negócio.

from sqlalchemy import select
from sqlalchemy.orm import Session

from acesso_api.models.historico_alerta import HistoricoAlerta


class HistoricoRepository:
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, historico: HistoricoAlerta) -> HistoricoAlerta:
        self.db.add(historico)
        self.db.commit()
        self.db.refresh(historico)
        return historico

    def listar_por_usuario(self, usuario_id: int) -> list[HistoricoAlerta]:
        """Alertas do usuário, do mais recente para o mais antigo."""
        consulta = (
            select(HistoricoAlerta)
            .where(HistoricoAlerta.usuario_id == usuario_id)
            .order_by(HistoricoAlerta.id.desc())
        )
        return list(self.db.scalars(consulta).all())
