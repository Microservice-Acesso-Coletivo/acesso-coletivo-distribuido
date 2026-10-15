# Ponto de partida da acesso_api (porta 8080), a porta de entrada do sistema.
# Cria o app FastAPI, cria as tabelas no SQLite, registra os handlers de erro,
# liga as rotas dos três Controllers e inicia o Consumer do RabbitMQ.

from contextlib import asynccontextmanager

from fastapi import FastAPI

from acesso_api.consumers.alerta_consumer import criar_consumidor
from acesso_api.controllers.alerta_controller import router as alerta_router
from acesso_api.controllers.parada_controller import router as parada_router
from acesso_api.controllers.usuario_controller import router as usuario_router
from acesso_api.database import Base, engine
from acesso_api.exceptions import registrar_handlers

# Cria as tabelas que ainda não existem. Os imports dos controllers acima já
# carregaram os Models HistoricoAlerta e SolicitacaoAlerta, então a Base
# conhece as tabelas.
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Liga o Consumer junto com o app e desliga junto com ele."""
    consumidores = [criar_consumidor()]
    for consumidor in consumidores:
        consumidor.start()
    yield
    for consumidor in consumidores:
        consumidor.parar()
    for consumidor in consumidores:
        consumidor.join(timeout=3)


app = FastAPI(title="Acesso Coletivo - API", lifespan=ciclo_de_vida)

registrar_handlers(app)
app.include_router(usuario_router)
app.include_router(parada_router)
app.include_router(alerta_router)
