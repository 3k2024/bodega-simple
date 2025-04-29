# main.py

from typing import Optional
from datetime import datetime, timedelta
import io

from fastapi import (
    FastAPI, Request, Depends, HTTPException, status,
    Form, Security, File, UploadFile
)
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlmodel import Session, select, delete

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from jose import jwt, JWTError

from database import init_db, get_session
from models import Guia, Item, EspecialidadEnum
from auth import (
    oauth2_scheme, verify_password, get_password_hash,
    create_access_token, SECRET_KEY, ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

from models import User
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select











# --- Inicialización de BD y App ---
init_db()
app = FastAPI(
    title="Bodega Internacional",
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

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

# --- Auth Helpers ---
def get_current_user(token: str = Depends(oauth2_scheme)):
    creds_exc = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str    = payload.get("role")
        if not username or not role:
            raise creds_exc
    except JWTError:
        raise creds_exc
    user = fake_users_db.get(username)
    if not user:
        raise creds_exc
    return {"username": username, "role": role}

def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Permiso denegado")
    return user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token = create_access_token(
        {"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}




#------LOGIN


@app.post("/login")
def login_usuario(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta"
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    )
    
    return {"access_token": access_token, "token_type": "bearer"}










# --- 1) Crear guía + primer ítem ---
@app.get("/", response_class=HTMLResponse)
def form_guia(request: Request):
    hoy = datetime.today().date().isoformat()
    esp = [e.value for e in EspecialidadEnum]
    return templates.TemplateResponse(
        "guia_form.html",
        {"request": request, "hoy": hoy, "error": None, "especialidades": esp}
    )

@app.post("/nueva-guia", response_class=HTMLResponse)
def nueva_guia(
    request: Request,
    id_guid: str       = Form(...),
    tag: str           = Form(...),
    descripcion: str   = Form(...),
    cantidad: int      = Form(...),
    fecha: str         = Form(...),
    proveedor: str     = Form(...),
    especialidad: str  = Form(...),
    observacion: str   = Form(...),
    db: Session        = Depends(get_session),
):
    # Validar campos
    if any(str(v).strip()=="" for v in [
        id_guid, tag, descripcion, fecha,
        proveedor, especialidad, observacion
    ]):
        esp = [e.value for e in EspecialidadEnum]
        return templates.TemplateResponse(
            "guia_form.html",
            {
              "request": request, "hoy": fecha,
              "error": "Todos los campos son obligatorios (cantidad puede ser 0).",
              "especialidades": esp
            }
        )
    if db.get(Guia, id_guid):
        esp = [e.value for e in EspecialidadEnum]
        return templates.TemplateResponse(
            "guia_form.html",
            {
              "request": request, "hoy": fecha,
              "error": "¡Guía duplicada!", "especialidades": esp
            }
        )
    # Insertar guía
    db.add(Guia(
        id_guid=id_guid, fecha=fecha,
        proveedor=proveedor, observacion=observacion
    ))
    db.commit()
    # Insertar primer ítem
    db.add(Item(
        tag=tag, descripcion=descripcion,
        cantidad=cantidad,
        especialidad=EspecialidadEnum(especialidad),
        id_guid=id_guid
    ))
    db.commit()
    return RedirectResponse(f"/guia/{id_guid}", status_code=303)


# --- 2) Ver guía y agregar ítems ---
@app.get("/guia/{id_guid}", response_class=HTMLResponse)
def ver_guia(id_guid: str, request: Request, db: Session = Depends(get_session)):
    guia = db.get(Guia, id_guid)
    if not guia:
        raise HTTPException(404, "Guía no encontrada")
    items = db.exec(select(Item).where(Item.id_guid==id_guid)).all()
    esp = [e.value for e in EspecialidadEnum]
    return templates.TemplateResponse(
        "item_form.html",
        {"request": request, "guia": guia, "items": items, "especialidades": esp}
    )

@app.post("/guia/{id_guid}/agregar-item")
def agregar_item(
    id_guid: str,
    tag: str            = Form(...),
    descripcion: str    = Form(...),
    cantidad: int       = Form(...),
    especialidad:Optional[str] = Form(None),
    db: Session         = Depends(get_session),
):
    db.add(Item(
        tag=tag, descripcion=descripcion,
        cantidad=cantidad,
        especialidad=EspecialidadEnum(especialidad) if especialidad else None,
        id_guid=id_guid
    ))
    db.commit()
    return RedirectResponse(f"/guia/{id_guid}", status_code=303)


# --- 3) Listado de guías ---
@app.get("/guias", response_class=HTMLResponse)
def listado(request: Request, db: Session = Depends(get_session)):
    guias_data = []
    for g in db.exec(select(Guia)).all():
        items = db.exec(select(Item).where(Item.id_guid==g.id_guid)).all()
        guias_data.append({
            "id_guid": g.id_guid,
            "fecha": g.fecha,
            "proveedor": g.proveedor,
            "items": items
        })
    return templates.TemplateResponse("guias_list.html",
                                      {"request": request, "guias": guias_data})


# --- 4) Confirmar y eliminar 1 guía ---
@app.get("/delete-guia/{id_guid}", response_class=HTMLResponse)
def confirm_delete(id_guid: str, request: Request, db: Session = Depends(get_session)):
    guia = db.get(Guia, id_guid)
    if not guia:
        raise HTTPException(404, "Guía no encontrada")
    return templates.TemplateResponse(
        "confirm_delete.html", {"request": request, "guia": guia}
    )

@app.post("/delete-guia/{id_guid}")
def delete_guia(id_guid: str, db: Session = Depends(get_session)):
    db.exec(delete(Item).where(Item.id_guid==id_guid))
    db.exec(delete(Guia).where(Guia.id_guid==id_guid))
    db.commit()
    return RedirectResponse("/guias", status_code=303)


# --- 5) Búsqueda y filtros ---
@app.get("/search", response_class=HTMLResponse)
def search(
    request: Request,
    id_guid: Optional[str]    = None,
    proveedor: Optional[str]  = None,
    date_from: Optional[str]  = None,
    date_to: Optional[str]    = None,
    db: Session               = Depends(get_session)
):
    stmt = select(Guia)
    if id_guid:
        stmt = stmt.where(Guia.id_guid==id_guid)
    if proveedor:
        stmt = stmt.where(Guia.proveedor.contains(proveedor))
    if date_from:
        stmt = stmt.where(Guia.fecha >= date_from)
    if date_to:
        stmt = stmt.where(Guia.fecha <= date_to)
    results = db.exec(stmt).all()
    return templates.TemplateResponse("search.html",
                                      {"request": request, "results": results})


# --- 6) Ingreso manual masivo ---
@app.get("/manual-import", response_class=HTMLResponse)
def manual_import_form(request: Request):
    return templates.TemplateResponse("manual_import.html",
                                      {"request": request, "error": None})

@app.post("/manual-import", response_class=HTMLResponse)
def manual_import_submit(
    request: Request,
    id_guid_data: str       = Form(...),
    tag_data: str           = Form(...),
    descripcion_data: str   = Form(...),
    cantidad_data: str      = Form(...),
    fecha_data: str         = Form(...),
    proveedor_data: str     = Form(None),
    observacion_data: str   = Form(None),
    db: Session             = Depends(get_session),
):
    id_guids = [x.strip() for x in id_guid_data.splitlines() if x.strip()]
    tags     = [x.strip() for x in tag_data.splitlines()    if x.strip()]
    descs    = [x.strip() for x in descripcion_data.splitlines() if x.strip()]
    cants    = [x.strip() for x in cantidad_data.splitlines()   if x.strip()]
    fechas   = [x.strip() for x in fecha_data.splitlines()      if x.strip()]
    provs    = [x.strip() for x in (proveedor_data or "").splitlines() if x.strip()]
    obs      = [x.strip() for x in (observacion_data or "").splitlines() if x.strip()]

    n = len(id_guids)
    if not (len(tags)==n and len(descs)==n and len(cants)==n and len(fechas)==n):
        return templates.TemplateResponse("manual_import.html",
            {"request": request,
             "error": "Todas las listas obligatorias deben tener el mismo número de líneas."}
        )
    for i in range(n):
        gid = id_guids[i]
        if not db.get(Guia, gid):
            db.add(Guia(
                id_guid=gid,
                fecha=fechas[i],
                proveedor=(provs[i] if i<len(provs) else None),
                observacion=(obs[i] if i<len(obs) else None)
            ))
            db.commit()
        db.add(Item(
            tag=tags[i],
            descripcion=descs[i],
            cantidad=int(cants[i]),
            id_guid=gid
        ))
    db.commit()
    return RedirectResponse("/guias", status_code=303)


# --- 7) Vaciar BD ---
@app.get("/reset", response_class=HTMLResponse)
def reset_form(request: Request):
    return templates.TemplateResponse("reset.html", {"request": request})

@app.post("/vaciar")
def vaciar_bd(db: Session = Depends(get_session)):
    db.exec(delete(Item))
    db.exec(delete(Guia))
    db.commit()
    return RedirectResponse("/", status_code=303)


# --- 8) Exportar Excel/PDF ---
@app.get("/export/excel")
def export_excel(db: Session = Depends(get_session)):
    rows = []
    for g in db.exec(select(Guia)).all():
        for it in db.exec(select(Item).where(Item.id_guid==g.id_guid)):
            rows.append({
                "Guía": g.id_guid,
                "Fecha": g.fecha,
                "Proveedor": g.proveedor,
                "TAG": it.tag,
                "Descripción": it.descripcion,
                "Cantidad": it.cantidad,
                "Especialidad": it.especialidad or ""
            })
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Bodega")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition":"attachment; filename=bodega.xlsx"}
    )

@app.get("/export/pdf")
def export_pdf(db: Session = Depends(get_session)):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 750
    for g in db.exec(select(Guia)).all():
        c.drawString(50, y, f"Guía {g.id_guid} — {g.fecha} — {g.proveedor or ''}")
        y -= 15
        for it in db.exec(select(Item).where(Item.id_guid==g.id_guid)):
            line = f"{it.tag} | {it.descripcion} | Cant: {it.cantidad}"
            if it.especialidad:
                line += f" | Esp: {it.especialidad}"
            c.drawString(70, y, line)
            y -= 12
            if y < 50:
                c.showPage(); y = 750
        y -= 10
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition":"attachment; filename=bodega.pdf"}
    )


# --- 9) Estadísticas para gráficos ---
@app.get("/api/stats")
def stats(db: Session = Depends(get_session)):
    data = {}
    for e in EspecialidadEnum:
        cnt = db.exec(select(Item).where(Item.especialidad==e)).count()
        data[e.value] = cnt
    return data


#----USUARIOS TEMPORAL

@app.post("/crear-bodega-user")
def crear_bodega_user(db: Session = Depends(get_session), user: dict = Depends(require_admin)):
    from models import User
    from auth import get_password_hash

    if db.exec(select(User).where(User.username == "bodega_user")).first():
        raise HTTPException(status_code=400, detail="Usuario ya existe")

    nuevo_user = User(
        username="bodega_user",
        hashed_password=get_password_hash("bodega123"),
        role="user"
    )
    db.add(nuevo_user)
    db.commit()
    return {"msg": "Usuario bodega_user creado exitosamente"}
