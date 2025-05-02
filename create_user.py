from sqlmodel import Session, select
from database import engine
from models import User
from auth import get_password_hash

def create_bodega_user():
    with Session(engine) as session:
        # Verificar si el usuario ya existe
        statement = select(User).where(User.username == "bodega_user")
        existing_user = session.exec(statement).first()

        if existing_user:
            print("El usuario bodega_user ya existe.")
            return

        # Crear el usuario bodega_user
        bodega_user = User(
            username="bodega_user",
            hashed_password=get_password_hash("bodega123"),  # Cambia la clave si quieres
            role="user"  # Rol de usuario regular
        )
        session.add(bodega_user)
        session.commit()
        print("Usuario bodega_user creado exitosamente.")

if __name__ == "__main__":
    create_bodega_user()
