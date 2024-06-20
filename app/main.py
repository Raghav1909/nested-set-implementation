from fastapi import FastAPI
from . import models, nodes
from app.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(nodes.router)