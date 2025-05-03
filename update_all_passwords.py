from sqlmodel import Session, select
from database import engine
from models import User
from auth import get_password_hash
from fastapi import FastAPI

app = FastAPI()

def update_all_passwords():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            # Actualiza las contraseñas al nuevo esquema
            user.hashed_password = get_password_hash("default_password")
            session.add(user)
        session.commit()
        print("Todas las contraseñas han sido actualizadas.")

@app.get("/update-passwords")
def update_passwords():
    update_all_passwords()
    return {"message": "Contraseñas actualizadas"}

if __name__ == "__main__":
    update_all_passwords()