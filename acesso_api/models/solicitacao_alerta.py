# Camada Model: pedido de alerta recebido pela API.
# Com a comunicação assíncrona, a API responde 202 antes de o alerta existir.
# Esta tabela guarda o pedido e acompanha o andamento: PENDENTE até chegar o
# evento do transporte_service, depois CONCLUIDA (com o resultado) ou FALHOU.

import enum
from datetime import datetime

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from acesso_api.database import Base
from acesso_api.models.historico_alerta import NivelAlerta, TipoAlerta


class StatusSolicitacao(str, enum.Enum):
    PENDENTE = "PENDENTE"
    CONCLUIDA = "CONCLUIDA"
    FALHOU = "FALHOU"


class SolicitacaoAlerta(Base):
    __tablename__ = "solicitacoes_alerta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Não é chave estrangeira: o usuário mora no banco de outro serviço.
    usuario_id: Mapped[int] = mapped_column(index=True)
    latitude: Mapped[float]
    longitude: Mapped[float]
    status: Mapped[StatusSolicitacao] = mapped_column(
        Enum(StatusSolicitacao), default=StatusSolicitacao.PENDENTE
    )
    # Resultado: só é preenchido quando o status vira CONCLUIDA.
    parada_nome: Mapped[str | None] = mapped_column(String(100), default=None)
    distancia_metros: Mapped[int | None] = mapped_column(default=None)
    nivel: Mapped[NivelAlerta | None] = mapped_column(Enum(NivelAlerta), default=None)
    tipo_alerta: Mapped[TipoAlerta | None] = mapped_column(Enum(TipoAlerta), default=None)
    mensagem: Mapped[str | None] = mapped_column(String(300), default=None)
    # Motivo: só é preenchido quando o status vira FALHOU.
    codigo_erro: Mapped[str | None] = mapped_column(String(50), default=None)
    motivo_falha: Mapped[str | None] = mapped_column(String(300), default=None)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.now)
    atualizado_em: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
