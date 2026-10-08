# Camada DTO (entrada): define o JSON e os parâmetros que o cliente pode enviar.
# A validação é feita aqui pelo Pydantic; se algo estiver errado, o FastAPI
# responde 422 antes mesmo de chegar no Controller.

from pydantic import BaseModel, Field


class ParadaRequest(BaseModel):
    """Usado tanto para criar (POST) quanto para atualizar (PUT) uma parada."""

    nome: str = Field(min_length=2, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    terminal: bool = False
    linhas: str = Field(default="", max_length=200)


class AlertaRequest(BaseModel):
    """Parâmetros de consulta de GET /paradas/alerta: quem é e onde está."""

    usuario_id: int = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
