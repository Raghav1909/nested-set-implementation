from fastapi import FastAPI
import models, nodes
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(nodes.router)