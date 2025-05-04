import os
from sqlmodel import SQLModel, create_engine, Session

# Configuración de la base de datos
DATABASE_URL = "sqlite:///bodega.db"  # Cambia esto si usas otra base de datos
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Inicializa la base de datos creando las tablas necesarias."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Obtiene una sesión de la base de datos."""
    with Session(engine) as session:
        yield session