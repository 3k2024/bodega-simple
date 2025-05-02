from sqlmodel import Session
from database import engine
from models import User
from auth import get_password_hash

def create_user(username: str, password: str, role: str):
    """Crea un nuevo usuario en la base de datos."""
    with Session(engine) as session:
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            hashed_password=hashed_password,
            role=role
        )
        session.add(new_user)
        session.commit()
        print(f"Usuario '{username}' creado con éxito.")

if __name__ == "__main__":
    # Cambia estos valores para crear usuarios
    create_user("admin", "adminpass", "admin")  # Usuario administrador
    create_user("compañero", "companero123", "user")  # Usuario para tu compañero
