from sqlmodel import Session, select
from db_config import engine
from models import User
from auth import get_password_hash

def list_users():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}")

def update_password(username: str, new_password: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f"Usuario {username} no encontrado.")
            return

        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        print(f"Contraseña actualizada para el usuario {username}.")

if __name__ == "__main__":
    update_password("admin", "adminpass")