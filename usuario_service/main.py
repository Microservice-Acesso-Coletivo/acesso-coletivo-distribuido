# Ponto de partida do usuario_service (porta 8081).
# Cria o app FastAPI, cria as tabelas no SQLite, registra o handler de
# erros e liga as rotas do Controller.

from fastapi import FastAPI

from usuario_service.controllers.usuario_controller import router as usuario_router
from usuario_service.database import Base, engine
from usuario_service.exceptions import registrar_handlers

# Cria as tabelas que ainda não existem. O import do controller acima já
# carregou o Model Usuario, então a Base conhece a tabela "usuarios".
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Acesso Coletivo - Serviço de Usuários")

registrar_handlers(app)
app.include_router(usuario_router)
