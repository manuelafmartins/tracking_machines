## main.py
#from fastapi import FastAPI
#from .database import Base, engine
#from .alarmes import iniciar_agendador
#
## Import dos routers
#from .routers import auth_router, empresas, maquinas, manutencoes
#
#Base.metadata.create_all(bind=engine)
#
#app = FastAPI(title="GestÃ£o de Frotas", description="API para gestÃ£o de camiÃµes e manutenÃ§Ã£o")
#
#app.include_router(auth_router.router)
#app.include_router(empresas.router)
#app.include_router(maquinas.router)
#app.include_router(manutencoes.router)
#
#iniciar_agendador()


# backend/main.py
from fastapi import FastAPI
from .database import Base, engine
from . import models
from .routers import empresas, maquinas, manutencoes
from .alarmes import iniciar_agendador

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(empresas.router)
app.include_router(maquinas.router)
app.include_router(manutencoes.router)

# Iniciamos o agendador quando a API sobe
#iniciar_agendador()

@app.get("/")
def home():
    return {"mensagem": "API de gestão de frotas em construção"}
