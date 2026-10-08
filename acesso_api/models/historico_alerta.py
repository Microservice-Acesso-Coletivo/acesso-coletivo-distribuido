# Camada Model: estrutura de dados central da acesso_api.
# HistoricoAlerta é mapeada para a tabela "historico_alertas" e guarda cada
# alerta gerado: quem pediu, onde estava e o que foi avisado.

import enum
from datetime import datetime

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from acesso_api.database import Base


class TipoAlerta(str, enum.Enum):
    """Como o usuário quer ser avisado. É também a preferência do cadastro."""

    AUDIO = "AUDIO"
    VIBRACAO = "VIBRACAO"
    AMBOS = "AMBOS"


class NivelAlerta(str, enum.Enum):
    """O quão perto a pessoa estava da parada."""

    LONGE = "LONGE"
    PROXIMO = "PROXIMO"
    DESEMBARQUE = "DESEMBARQUE"


class HistoricoAlerta(Base):
    __tablename__ = "historico_alertas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Não é chave estrangeira: o usuário mora no banco de outro serviço.
    usuario_id: Mapped[int] = mapped_column(index=True)
    latitude: Mapped[float]
    longitude: Mapped[float]
    parada_nome: Mapped[str] = mapped_column(String(100))
    distancia_metros: Mapped[int]
    nivel: Mapped[NivelAlerta] = mapped_column(Enum(NivelAlerta))
    tipo_alerta: Mapped[TipoAlerta] = mapped_column(Enum(TipoAlerta))
    # Preenchido sozinho no momento da gravação, com a hora local do servidor.
    criado_em: Mapped[datetime] = mapped_column(default=datetime.now)
