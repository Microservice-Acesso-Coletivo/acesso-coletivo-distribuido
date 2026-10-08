# Ponto de partida do transporte_service (porta 8082).
# Cria o app FastAPI, cria as tabelas no SQLite, faz a carga inicial de
# paradas, registra o handler de erros e liga as rotas do Controller.

from fastapi import FastAPI

from transporte_service.controllers.parada_controller import router as parada_router
from transporte_service.database import Base, engine
from transporte_service.exceptions import registrar_handlers
from transporte_service.services.carga_inicial import carregar_paradas_iniciais

# Cria as tabelas que ainda não existem. O import do controller acima já
# carregou o Model Parada, então a Base conhece a tabela "paradas".
Base.metadata.create_all(bind=engine)
carregar_paradas_iniciais()

app = FastAPI(title="Acesso Coletivo - Serviço de Transporte")

registrar_handlers(app)
app.include_router(parada_router)
