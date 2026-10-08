# Camada Repository: única parte do serviço que fala com o banco.
# Contém o CRUD e as consultas de Parada. Não valida regra de negócio,
# só grava, busca e remove.

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from transporte_service.models.parada import Parada


class ParadaRepository:
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, parada: Parada) -> Parada:
        """Insere uma parada nova ou grava as alterações de uma existente."""
        self.db.add(parada)
        self.db.commit()
        self.db.refresh(parada)
        return parada

    def buscar_por_id(self, parada_id: int) -> Parada | None:
        return self.db.get(Parada, parada_id)

    def listar(self) -> list[Parada]:
        consulta = select(Parada).order_by(Parada.id)
        return list(self.db.scalars(consulta).all())

    def contar(self) -> int:
        consulta = select(func.count()).select_from(Parada)
        return self.db.scalar(consulta)

    def remover(self, parada: Parada) -> None:
        self.db.delete(parada)
        self.db.commit()
