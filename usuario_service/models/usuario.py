# Camada Model: estrutura de dados central do serviço.
# A classe Usuario é mapeada para a tabela "usuarios" do banco.
# Só descreve os dados, não tem regra de negócio.

import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from usuario_service.database import Base


class PreferenciaAlerta(str, enum.Enum):
    """Como a pessoa quer ser avisada da proximidade da parada."""

    AUDIO = "AUDIO"
    VIBRACAO = "VIBRACAO"
    AMBOS = "AMBOS"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(200))
    preferencia_alerta: Mapped[PreferenciaAlerta] = mapped_column(Enum(PreferenciaAlerta))
