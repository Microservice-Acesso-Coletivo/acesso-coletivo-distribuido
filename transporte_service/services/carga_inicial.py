# Camada Service (apoio): carga inicial de paradas e terminais de Teresina.
# Roda quando o serviço sobe e só grava se a tabela estiver vazia, para o
# sistema já ter dados na primeira execução.

from transporte_service.database import SessionLocal
from transporte_service.models.parada import Parada
from transporte_service.repositories.parada_repository import ParadaRepository

# Coordenadas aproximadas e linhas ilustrativas, suficientes para demonstrar o alerta.
PARADAS_INICIAIS = [
    {"nome": "Terminal Dirceu", "latitude": -5.1069, "longitude": -42.7527, "terminal": True, "linhas": "401,402,610"},
    {"nome": "Terminal Norte", "latitude": -5.0450, "longitude": -42.8200, "terminal": True, "linhas": "101,104,201"},
    {"nome": "Terminal Sul", "latitude": -5.1480, "longitude": -42.7900, "terminal": True, "linhas": "501,503,620"},
    {"nome": "Terminal Leste", "latitude": -5.0560, "longitude": -42.7650, "terminal": True, "linhas": "301,305,630"},
    {"nome": "Terminal Rodoviário", "latitude": -5.1090, "longitude": -42.7870, "terminal": True, "linhas": "030,520"},
    {"nome": "Praça Rio Branco", "latitude": -5.0903, "longitude": -42.8195, "terminal": False, "linhas": "030,101,401"},
    {"nome": "Praça da Bandeira", "latitude": -5.0915, "longitude": -42.8215, "terminal": False, "linhas": "101,501"},
]


def carregar_paradas_iniciais() -> None:
    """Grava as paradas iniciais se ainda não houver nenhuma cadastrada."""
    db = SessionLocal()
    try:
        repository = ParadaRepository(db)
        if repository.contar() > 0:
            return
        for dados in PARADAS_INICIAIS:
            repository.salvar(Parada(**dados))
    finally:
        db.close()
