from sqlmodel import Session
from database import engine
from models import User
from auth import get_password_hash

def create_admin_user():
    with Session(engine) as session:
        # Crear el usuario administrador
        admin_user = User(
            username="hernan_admin",       # Puedes cambiarlo si quieres
            hashed_password=get_password_hash("adminpass123"),  # Cambia la clave si quieres
            role="admin"
        )
        session.add(admin_user)
        session.commit()
        print("Usuario administrador creado exitosamente.")

if __name__ == "__main__":
    create_admin_user()
