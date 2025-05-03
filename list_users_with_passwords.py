from sqlmodel import Session, select
from db_config import engine
from models import User
from auth import get_password_hash  # Importa la función para generar hashes

def list_users_with_passwords():
    """
    Lista todos los usuarios en la base de datos junto con sus contraseñas en formato hash.
    """
    try:
        # Hash de referencia para la contraseña "hola"
        reference_hash = get_password_hash("hola")
        print(f"[INFO] Hash de referencia para 'hola': {reference_hash}")

        with Session(engine) as session:
            users = session.exec(select(User)).all()
            if not users:
                print("[INFO] No se encontraron usuarios en la base de datos.")
                return

            print("[INFO] Usuarios encontrados:")
            for user in users:
                match_status = "Coincide" if user.hashed_password == reference_hash else "No coincide"
                print(f"ID: {user.id}, Username: {user.username}, Hashed Password: {user.hashed_password}, Match: {match_status}")
    except Exception as e:
        print(f"[ERROR] Error al listar los usuarios: {e}")
    finally:
        print("[INFO] Finalizando la operación.")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña ingresada coincide con el hash almacenado.
    """
    try:
        # Genera el hash de la contraseña ingresada
        generated_hash = get_password_hash(plain_password)
        print(f"[DEBUG] Contraseña ingresada: {plain_password}")
        print(f"[DEBUG] Hash generado: {generated_hash}")
        print(f"[DEBUG] Hash almacenado en la base de datos: {hashed_password}")
        
        # Compara los hashes directamente
        if generated_hash == hashed_password:
            print("[DEBUG] La contraseña es válida.")
            return True
        else:
            print("[DEBUG] La contraseña es inválida.")
            return False
    except Exception as e:
        print(f"[ERROR] Error al verificar la contraseña: {e}")
        return False

if __name__ == "__main__":
    list_users_with_passwords()

    # En el controlador de inicio de sesión
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == "example_user")).first()
        password = "example_password"
        if user:
            print(f"[DEBUG] Usuario encontrado: {user.username}")
            print(f"[DEBUG] Hash almacenado en la base de datos: {user.hashed_password}")
            print(f"[DEBUG] Contraseña ingresada: {password}")