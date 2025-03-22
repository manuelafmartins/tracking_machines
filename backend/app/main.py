from fastapi import FastAPI
from .routers import auth_router, empresas, maquinas, manutencoes
from .database import Base, engine
from .alarmes import iniciar_agendador

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestão de Frotas", description="API para gestão de camiões e manutenção")

app.include_router(auth_router.router)
app.include_router(empresas.router)
app.include_router(maquinas.router)
app.include_router(manutencoes.router)

iniciar_agendador()
