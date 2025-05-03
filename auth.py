# auth.py
import os
import hashlib
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "clave_por_defecto")  # Usa una variable de entorno
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))  # Configurable por entorno

def get_password_hash(password: str) -> str:
    """
    Genera un hash SHA-256 de la contraseña.
    """
    hashed = hashlib.sha256(password.encode()).hexdigest()
    print(f"[DEBUG] Hash generado para '{password}': {hashed}")
    return hashed

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """
    Crea un token de acceso JWT con datos y tiempo de expiración.
    """
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except JWTError as e:
        print(f"[ERROR] Error al generar el token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el token de acceso"
        )

if __name__ == "__main__":
    # Código de prueba
    # En el controlador de inicio de sesión
    print(f"[DEBUG] Usuario encontrado: {user.username}")
    print(f"[DEBUG] Hash almacenado en la base de datos: {user.hashed_password}")
    print(f"[DEBUG] Contraseña ingresada: {password}")
