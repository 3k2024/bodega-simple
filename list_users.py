from sqlmodel import Session, select
from database import engine
from models import User

def list_users():
    """Lista todos los usuarios registrados en la base de datos."""
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            print(f"Usuario: {user.username}, Rol: {user.role}")

if __name__ == "__main__":
    list_users()