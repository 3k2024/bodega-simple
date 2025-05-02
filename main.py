# main.py
from typing import Optional
from datetime import datetime, timedelta
import os  # Asegúrate de importar os
from fastapi import (
    FastAPI, Request, Depends, HTTPException, status,
    Form, Security, File, UploadFile, Cookie
)
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select, delete
from jose import jwt, JWTError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler
import uvicorn
from database import init_db, get_session
from models import Guia, Item, EspecialidadEnum, User
from auth import (
    oauth2_scheme, verify_password, get_password_hash,
    create_access_token, SECRET_KEY, ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# --- Inicialización de BD y App ---
init_db()
app = FastAPI(
    title="Bodega Internacional",
    docs_url="/docs",  # Habilita la documentación en /docs
    redoc_url="/redoc",  # Habilita la documentación alternativa en /redoc
    openapi_url="/api/openapi.json"  # Esquema OpenAPI en esta ruta
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# --- Ruta de prueba ---
@app.get("/ping")
def ping():
    return {"message": "pong"}

# --- Usuarios de ejemplo (in-memory) ---
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("adminpass"),
        "role": "admin"
    },
    "user": {
        "username": "user",
        "hashed_password": get_password_hash("userpass"),
        "role": "user"
    }
}

# --- Funciones auxiliares ---
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    access_token_cookie: Optional[str] = Cookie(None),
    db: Session = Depends(get_session)
):
    token_to_use = token or (access_token_cookie.replace("Bearer ", "") if access_token_cookie else None)
    if not token_to_use:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='No autorizado')

    try:
        payload = jwt.decode(token_to_use, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='No autorizado')
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='No autorizado')

    user = db.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='No autorizado')

    return {"username": user.username, "role": user.role}

def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Permiso denegado")
    return user

# --- Rutas ---
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    user = db.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_usuario(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    user = db.exec(select(User).where(User.username == username)).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales inválidas"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/", response_class=HTMLResponse)
def form_guia(request: Request, user: dict = Depends(get_current_user)):
    hoy = datetime.today().date().isoformat()
    esp = [e.value for e in EspecialidadEnum]
    return templates.TemplateResponse(
        "guia_form.html",
        {"request": request, "hoy": hoy, "error": None, "especialidades": esp, "user": user["username"]}
    )

# --- Manejo de errores ---
@app.exception_handler(StarletteHTTPException)
async def redirect_on_401(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login", status_code=303)
    return await http_exception_handler(request, exc)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render asigna el puerto a través de la variable PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port)