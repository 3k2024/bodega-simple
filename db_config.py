from sqlmodel import SQLModel, create_engine, Session

# Configuración de la base de datos
DATABASE_URL = "sqlite:///bodega.db"  # Cambia esto si usas otra base de datos
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Inicializa la base de datos creando las tablas necesarias."""
    try:
        SQLModel.metadata.create_all(engine)
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

def get_session():
    """Obtiene una sesión de la base de datos."""
    with Session(engine) as session:
        yield session