import os
from sqlmodel import SQLModel, create_engine, Session
from models import Guia, Item, User  # 👈 Aquí traemos también User

# Usar una variable de entorno para la cadena de conexión
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bodega.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def init_db():
    """
    Inicializa la base de datos creando todas las tablas definidas en los modelos.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Generador para manejar sesiones de base de datos.
    """
    with Session(engine) as session:
        yield session
