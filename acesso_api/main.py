# Ponto de partida da acesso_api (porta 8080), a porta de entrada do sistema.
# Cria o app FastAPI, cria a tabela do histórico no SQLite, registra os
# handlers de erro e liga as rotas dos três Controllers.

from fastapi import FastAPI

from acesso_api.controllers.alerta_controller import router as alerta_router
from acesso_api.controllers.parada_controller import router as parada_router
from acesso_api.controllers.usuario_controller import router as usuario_router
from acesso_api.database import Base, engine
from acesso_api.exceptions import registrar_handlers

# Cria as tabelas que ainda não existem. Os imports dos controllers acima já
# carregaram o Model HistoricoAlerta, então a Base conhece a tabela.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Acesso Coletivo - API")

registrar_handlers(app)
app.include_router(usuario_router)
app.include_router(parada_router)
app.include_router(alerta_router)
