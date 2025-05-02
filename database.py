import os
from sqlmodel import SQLModel, create_engine, Session
from models import Guia, Item, User

# Usar una variable de entorno para la cadena de conexión
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bodega.db")  # Cambia esto si usas PostgreSQL
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
