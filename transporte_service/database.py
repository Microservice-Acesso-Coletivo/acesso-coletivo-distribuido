# Configuração do banco de dados do transporte_service.
# Cria a conexão com o SQLite (arquivo ./data/transporte.db) e entrega uma
# sessão por requisição para quem precisar (Repository).

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

PASTA_DADOS = "data"
URL_BANCO = f"sqlite:///./{PASTA_DADOS}/transporte.db"

os.makedirs(PASTA_DADOS, exist_ok=True)

# check_same_thread=False: o FastAPI atende endpoints síncronos em threads
# diferentes, e o SQLite por padrão recusa conexões usadas fora da thread de origem.
engine = create_engine(URL_BANCO, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Classe base de todos os Models (tabelas) deste serviço."""


def get_db():
    """Abre uma sessão para a requisição e garante que ela seja fechada no final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
