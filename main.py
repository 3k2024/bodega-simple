# main.py
from typing import Optional
from datetime import datetime, timedelta
import os  # Asegúrate de importar os
from fastapi import (
    FastAPI, Request, Depends, HTTPException, status,
    Form, Security, File, UploadFile, Cookie
)
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse, FileResponse
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

@app.get("/click_ingreso_guia", response_class=HTMLResponse)
def mostrar_formulario_ingreso_guia(request: Request):
    return templates.TemplateResponse("ingreso_guia.html", {"request": request})

@app.post("/click_ingreso_guia")
async def guardar_guia_manual(
    id_guid: str = Form(...),
    fecha: str = Form(...),
    tag: str = Form(...),
    descripcion: str = Form(...),
    cantidad: int = Form(...),
    proveedor: Optional[str] = Form(None),
    observacion: Optional[str] = Form(None),
    especialidad: Optional[str] = Form(None),
    db: Session = Depends(get_session)
):
    try:
        print(f"Datos recibidos: id_guid={id_guid}, fecha={fecha}, tag={tag}, descripcion={descripcion}, cantidad={cantidad}, proveedor={proveedor}, observacion={observacion}, especialidad={especialidad}")

        # Validar y convertir el campo fecha
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()  # Convertir a objeto date
            print(f"Fecha convertida correctamente: {fecha_obj}")
        except ValueError as e:
            print(f"Error al convertir la fecha: {e}")
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD.")

        # Crear o buscar la guía
        guia = db.exec(select(Guia).where(Guia.id_guid == id_guid)).first()
        if not guia:
            print("Guía no encontrada, creando una nueva.")
            guia = Guia(
                id_guid=id_guid,
                fecha=fecha_obj,  # Asegúrate de usar fecha_obj
                proveedor=proveedor,
                observacion=observacion
            )
            db.add(guia)

        # Crear el ítem
        print("Creando el ítem asociado.")
        item = Item(
            tag=tag,
            descripcion=descripcion,
            cantidad=cantidad,
            id_guid=id_guid,
            especialidad=especialidad
        )
        db.add(item)

        db.commit()
        print("Guía y ítem guardados correctamente.")
        return {"message": "Guía guardada correctamente."}
    except Exception as e:
        print(f"Error al guardar la guía: {e}")
        raise HTTPException(status_code=500, detail=f"Error al guardar la guía: {str(e)}")

@app.get("/export-excel/")
def exportar_guias_a_excel(db: Session = Depends(get_session)):
    try:
        # Obtener las guías y sus ítems
        guias = db.exec(select(Guia)).all()
        data = []
        for guia in guias:
            for item in guia.items:
                data.append({
                    "Número de Guía": guia.id_guid,
                    "Fecha": guia.fecha,
                    "Proveedor": guia.proveedor,
                    "Observación": guia.observacion,
                    "TAG": item.tag,
                    "Descripción": item.descripcion,
                    "Cantidad": item.cantidad,
                    "Especialidad": item.especialidad
                })

        # Crear un DataFrame de pandas
        df = pd.DataFrame(data)

        # Guardar el archivo Excel
        file_path = "guias_exportadas.xlsx"
        df.to_excel(file_path, index=False)

        # Retornar el archivo como respuesta
        return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="guias_exportadas.xlsx")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar las guías: {str(e)}")

@app.get("/manual-import", response_class=HTMLResponse)
def mostrar_formulario_import(request: Request):
    print("Renderizando manual_import.html")
    return templates.TemplateResponse("manual_import.html", {"request": request})

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
    fecha=fecha.date(),  # ✅ convertir correctamente
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

@app.post("/manual-import")
async def procesar_importacion_manual(
    id_guid_data: str = Form(...),
    tag_data: str = Form(...),
    descripcion_data: str = Form(...),
    cantidad_data: str = Form(...),
    fecha_data: str = Form(...),
    proveedor_data: str = Form(None),
    observacion_data: str = Form(None),
    db: Session = Depends(get_session)
):
    try:
        # Dividir los datos por líneas
        id_guids = id_guid_data.splitlines()
        tags = tag_data.splitlines()
        descripciones = descripcion_data.splitlines()
        cantidades = cantidad_data.splitlines()
        fechas = fecha_data.splitlines()
        proveedores = proveedor_data.splitlines() if proveedor_data else [None] * len(id_guids)
        observaciones = observacion_data.splitlines() if observacion_data else [None] * len(id_guids)

        # Validar que todas las listas tengan la misma longitud
        if not (len(id_guids) == len(tags) == len(descripciones) == len(cantidades) == len(fechas)):
            raise HTTPException(status_code=400, detail="Las columnas no tienen la misma cantidad de filas.")

        # Procesar cada registro
        for i in range(len(id_guids)):
            try:
                # Convertir la fecha al formato correcto
                fecha_obj = datetime.strptime(fechas[i].strip(), "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Formato de fecha inválido en la línea {i + 1}. Use DD/MM/YYYY.")

            # Crear o buscar la guía
            guia = db.exec(select(Guia).where(Guia.id_guid == id_guids[i].strip())).first()
            if not guia:
                guia = Guia(
                    id_guid=id_guids[i].strip(),
                    fecha=fecha_obj,
                    proveedor=proveedores[i].strip() if proveedores[i] else None,
                    observacion=observaciones[i].strip() if observaciones[i] else None
                )
                db.add(guia)

            # Crear el ítem
            item = Item(
                tag=tags[i].strip(),
                descripcion=descripciones[i].strip(),
                cantidad=int(cantidades[i].strip()),
                id_guid=id_guids[i].strip()
            )
            db.add(item)

        db.commit()
        return {"message": f"Importación completada: {len(id_guids)} registros procesados."}

    except Exception as e:
        print(f"Error al procesar la importación: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la importación: {str(e)}")

@app.post("/upload-excel")
async def procesar_excel_asignado(
    file: str = Form(...),
    col_id_guid: str = Form(...),
    col_fecha: str = Form(...),
    col_tag: str = Form(...),
    col_descripcion: str = Form(...),
    col_cantidad: str = Form(...),
    col_proveedor: Optional[str] = Form(None),
    col_observacion: Optional[str] = Form(None),
    db: Session = Depends(get_session)
):
    try:
        # Leer el archivo Excel desde la ruta proporcionada
        df = pd.read_excel(file)

        # Procesar los datos según las columnas asignadas
        for _, row in df.iterrows():
            gid = row[col_id_guid]
            fecha = datetime.strptime(row[col_fecha], "%Y-%m-%d")
            tag = row[col_tag]
            descripcion = row[col_descripcion]
            cantidad = int(row[col_cantidad])
            proveedor = row[col_proveedor] if col_proveedor else None
            observacion = row[col_observacion] if col_observacion else None

            # Crear o buscar la guía
            guia = db.exec(select(Guia).where(Guia.id_guid == gid)).first()
            if not guia:
                guia = Guia(
                    id_guid=gid,
                    fecha=fecha,
                    proveedor=proveedor
                )
                db.add(guia)

            # Crear el ítem
            item = Item(
                tag=tag,
                descripcion=descripcion,
                cantidad=cantidad,
                id_guid=gid,
                observacion=observacion
            )
            db.add(item)

        db.commit()
        return {"message": "Datos importados correctamente."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

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