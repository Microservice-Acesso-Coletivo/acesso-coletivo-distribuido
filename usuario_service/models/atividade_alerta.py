# Camada Model: resumo da atividade de alertas de cada usuário.
# É alimentada pelos eventos "alerta.gerado" que chegam pelo broker, sem o
# usuario_service precisar chamar ninguém: uma linha por usuário, atualizada
# a cada alerta recebido.

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from usuario_service.database import Base


class AtividadeAlerta(Base):
    __tablename__ = "atividade_alertas"

    # Mesmo id do usuário. Não é autoincremento nem chave estrangeira formal.
    usuario_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    total_alertas: Mapped[int] = mapped_column(default=0)
    ultima_parada: Mapped[str] = mapped_column(String(100))
    ultimo_nivel: Mapped[str] = mapped_column(String(20))
    ultimo_alerta_em: Mapped[datetime]
    # Id do último evento aplicado: evita contar duas vezes a mesma mensagem reentregue.
    ultimo_evento_id: Mapped[str] = mapped_column(String(36))
