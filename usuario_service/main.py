# Ponto de partida do usuario_service (porta 8081).
# Cria o app FastAPI, cria as tabelas no SQLite, registra o handler de
# erros, liga as rotas dos Controllers e inicia o Consumer do RabbitMQ.

from contextlib import asynccontextmanager

from fastapi import FastAPI

from usuario_service.consumers.alerta_consumer import criar_consumidor
from usuario_service.controllers.atividade_controller import router as atividade_router
from usuario_service.controllers.usuario_controller import router as usuario_router
from usuario_service.database import Base, engine
from usuario_service.exceptions import registrar_handlers

# Cria as tabelas que ainda não existem. Os imports acima já carregaram os
# Models Usuario e AtividadeAlerta, então a Base conhece as tabelas.
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


app = FastAPI(title="Acesso Coletivo - Serviço de Usuários", lifespan=ciclo_de_vida)

registrar_handlers(app)
app.include_router(usuario_router)
app.include_router(atividade_router)
