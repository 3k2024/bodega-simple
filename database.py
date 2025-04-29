from sqlmodel import SQLModel, create_engine, Session
from models import Guia, Item, User  # 👈 Aquí traemos también User

engine = create_engine(
    "sqlite:///./bodega.db",
    connect_args={"check_same_thread": False}
)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
