# Camada Repository: única parte do serviço que fala com o banco.
# Grava e busca o resumo de atividade de alertas. Não valida regra de negócio.

from sqlalchemy.orm import Session

from usuario_service.models.atividade_alerta import AtividadeAlerta


class AtividadeRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_usuario(self, usuario_id: int) -> AtividadeAlerta | None:
        return self.db.get(AtividadeAlerta, usuario_id)

    def salvar(self, atividade: AtividadeAlerta) -> AtividadeAlerta:
        """Insere o resumo de um usuário novo ou grava as alterações do existente."""
        self.db.add(atividade)
        self.db.commit()
        self.db.refresh(atividade)
        return atividade
