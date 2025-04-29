from sqlmodel import Session
from database import engine
from models import User
from auth import get_password_hash

def create_bodega_user():
    with Session(engine) as session:
        bodega_user = User(
            username="bodega_user",
            hashed_password=get_password_hash("bodega123"),  # Puedes cambiar la clave si quieres
            role="user"  # 👈 IMPORTANTE: ahora es 'user', no 'admin'
        )
        session.add(bodega_user)
        session.commit()
        print("Usuario bodega_user creado exitosamente.")

if __name__ == "__main__":
    create_bodega_user()
