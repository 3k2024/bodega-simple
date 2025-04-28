from sqlmodel import SQLModel, create_engine, Session

engine = create_engine(
    "sqlite:///./bodega.db",
    connect_args={"check_same_thread": False}
)

def init_db():
    from models import Guia, Item
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
