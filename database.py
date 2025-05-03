import os
from sqlmodel import SQLModel, create_engine, Session
from models import Guia, Item, User  # Asegúrate de importar todos los modelos necesarios

# Usar una variable de entorno para la cadena de conexión
DATABASE_URL = "sqlite:///bodega.db"

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Inicializa la base de datos creando las tablas necesarias."""
    try:
        # Crear todas las tablas definidas en los modelos
        SQLModel.metadata.create_all(engine)
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

def get_session():
    """Obtiene una sesión de la base de datos."""
    with Session(engine) as session:
        yield session
