from db_config import engine
from sqlmodel import SQLModel

# Elimina todas las tablas
SQLModel.metadata.drop_all(engine)
print("Tablas eliminadas.")