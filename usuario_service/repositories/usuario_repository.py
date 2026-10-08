# Camada Repository: única parte do serviço que fala com o banco.
# Contém o CRUD e as consultas de Usuario. Não valida regra de negócio,
# só grava, busca e remove.

from sqlalchemy import select
from sqlalchemy.orm import Session

from usuario_service.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, usuario: Usuario) -> Usuario:
        """Insere um usuário novo ou grava as alterações de um existente."""
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def buscar_por_email(self, email: str) -> Usuario | None:
        consulta = select(Usuario).where(Usuario.email == email)
        return self.db.scalars(consulta).first()

    def listar(self) -> list[Usuario]:
        consulta = select(Usuario).order_by(Usuario.id)
        return list(self.db.scalars(consulta).all())

    def remover(self, usuario: Usuario) -> None:
        self.db.delete(usuario)
        self.db.commit()
