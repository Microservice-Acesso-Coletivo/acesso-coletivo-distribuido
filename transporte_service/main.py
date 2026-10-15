# Ponto de partida do transporte_service (porta 8082).
# Cria o app FastAPI, cria as tabelas no SQLite, faz a carga inicial de
# paradas, registra o handler de erros, liga as rotas do Controller e inicia
# o Consumer do RabbitMQ.

from contextlib import asynccontextmanager

from fastapi import FastAPI

from transporte_service.consumers.alerta_consumer import criar_consumidor
from transporte_service.controllers.parada_controller import router as parada_router
from transporte_service.database import Base, engine
from transporte_service.exceptions import registrar_handlers
from transporte_service.services.carga_inicial import carregar_paradas_iniciais

# Cria as tabelas que ainda não existem. O import do controller acima já
# carregou o Model Parada, então a Base conhece a tabela "paradas".
Base.metadata.create_all(bind=engine)
carregar_paradas_iniciais()


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


app = FastAPI(title="Acesso Coletivo - Serviço de Transporte", lifespan=ciclo_de_vida)

registrar_handlers(app)
app.include_router(parada_router)
