# Camada Model: estrutura de dados central do serviço.
# A classe Parada é mapeada para a tabela "paradas" do banco e representa
# tanto uma parada comum quanto um terminal de integração.

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from transporte_service.database import Base


class Parada(Base):
    __tablename__ = "paradas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float]
    longitude: Mapped[float]
    terminal: Mapped[bool] = mapped_column(default=False)
    # Códigos das linhas que passam na parada, separados por vírgula. Ex: "030,101".
    linhas: Mapped[str] = mapped_column(String(200), default="")
