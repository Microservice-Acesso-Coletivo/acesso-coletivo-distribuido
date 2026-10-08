# DTO do Client: o pedaço da resposta do usuario_service que interessa aqui.
# É uma cópia própria do contrato, porque microsserviços não compartilham
# código: cada um conhece o outro só pelo JSON.

import enum

from pydantic import BaseModel


class TipoAlerta(str, enum.Enum):
    """Como o usuário quer ser avisado (vem da preferência cadastrada)."""

    AUDIO = "AUDIO"
    VIBRACAO = "VIBRACAO"
    AMBOS = "AMBOS"


class UsuarioExterno(BaseModel):
    # Campos extras do JSON (como o email) são simplesmente ignorados.
    id: int
    nome: str
    preferencia_alerta: TipoAlerta
