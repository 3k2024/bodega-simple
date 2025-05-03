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
from database import init_db, get_session, engine
from models import Guia, Item, EspecialidadEnum, User
from auth import (
    oauth2_scheme, get_password_hash,
    SECRET_KEY, ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES, verify_password
)
from passlib.context import CryptContext
import pandas as pd

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Error al verificar la contraseña: {e}")
        return False

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Cookie(None),
    db: Session = Depends(get_session)
):
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    # Elimina el prefijo "Bearer " del token si existe
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="No autenticado")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user

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
        print("Credenciales inválidas en /token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    print(f"Token generado: {access_token}")
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
            status_code=401
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def form_guia(request: Request, user: dict = Depends(get_current_user)):
    hoy = datetime.today().date().isoformat()
    esp = [e.value for e in EspecialidadEnum]
    return templates.TemplateResponse(
        "guia_form.html",
        {"request": request, "hoy": hoy, "error": None, "especialidades": esp, "user": user["username"]}
    )

@app.post("/manual-import/")
async def manual_import(file: UploadFile = File(...)):
    try:
        # Leer el archivo Excel
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

        # Validar columnas requeridas
        columnas_requeridas = {'GD', 'Fecha', 'Proveedor', 'TAG', 'Descripcion Material', 'Cantidad'}
        if not columnas_requeridas.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"Faltan columnas requeridas: {', '.join(columnas_requeridas)}")

        # Procesar datos e insertar en la base de datos
        with Session(engine) as session:
            for _, row in df.iterrows():
                # Validar fecha
                try:
                    fecha = datetime.strptime(row["Fecha"], "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Fecha inválida: {row['Fecha']}")

                # Validar cantidad
                if not isinstance(row["Cantidad"], (int, float)):
                    raise HTTPException(status_code=400, detail=f"Cantidad inválida: {row['Cantidad']}")

                gid = str(row['GD']).strip()
                guia = session.get(Guia, gid)
                if not guia:
                    guia = Guia(
                        id_guid=gid,
                        fecha=str(fecha),
                        proveedor=row.get('Proveedor', None)
                    )
                    session.add(guia)

                item = Item(
                    tag=row['TAG'],
                    descripcion=row['Descripcion Material'],
                    cantidad=int(row['Cantidad']),
                    id_guid=gid
                )
                session.add(item)

            session.commit()

        return {"message": f"Importación completada: {len(df)} registros procesados."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

@app.get("/manual-import", response_class=HTMLResponse)
def mostrar_formulario_import(request: Request):
    return templates.TemplateResponse("manual_import.html", {"request": request})

# --- Manejo de errores ---
@app.exception_handler(StarletteHTTPException)
async def redirect_on_401(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        print("Redirigiendo a /login debido a error 401")
        return RedirectResponse(url="/login", status_code=303)
    return await http_exception_handler(request, exc)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render asigna el puerto a través de la variable PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port)