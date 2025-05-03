from sqlmodel import Session, select
from database import engine
from models import User
from auth import get_password_hash

def update_password(username: str, new_password: str):
    """
    Actualiza la contraseña de un usuario específico en la base de datos.
    """
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f"Usuario {username} no encontrado.")
            return

        # Genera el hash de la nueva contraseña
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        print(f"Contraseña actualizada para el usuario {username}.")

if __name__ == "__main__":
    update_password("hernan_admin", "hola")