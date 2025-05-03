from sqlmodel import Session, select
from database import engine
from models import User
from auth import get_password_hash

def create_admin_user():
    with Session(engine) as session:
        # Verifica si el usuario ya existe
        statement = select(User).where(User.username == "admin")
        user = session.exec(statement).first()
        if user:
            print("El usuario admin ya existe.")
            return

        # Crear el usuario administrador
        admin_user = User(
            username="admin",  # Cambia el nombre de usuario si lo deseas
            hashed_password=get_password_hash("adminpass"),  # Cambia la contraseña si lo deseas
            role="admin"
        )
        session.add(admin_user)
        session.commit()
        print("Usuario admin creado exitosamente.")

if __name__ == "__main__":
    create_admin_user()
