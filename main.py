from typing import Optional
from datetime import datetime, timedelta
import os
from fastapi import FastAPI, Request, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from db_config import init_db
from models import Guia, Item

# --- Inicialización de BD y App ---
init_db()
app = FastAPI(
    title="Bodega Internacional",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Rutas ---
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
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        guia = db.exec(select(Guia).where(Guia.id_guid == id_guid)).first()
        if not guia:
            guia = Guia(
                id_guid=id_guid,
                fecha=fecha_obj,
                proveedor=proveedor,
                observacion=observacion
            )
            db.add(guia)

        item = Item(
            tag=tag,
            descripcion=descripcion,
            cantidad=cantidad,
            id_guid=id_guid,
            especialidad=especialidad
        )
        db.add(item)
        db.commit()
        return {"message": "Guía guardada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la guía: {str(e)}")

@app.get("/export-excel/")
def exportar_guias_a_excel(db: Session = Depends(get_session)):
    try:
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

        import pandas as pd
        df = pd.DataFrame(data)
        file_path = "guias_exportadas.xlsx"
        df.to_excel(file_path, index=False)
        return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="guias_exportadas.xlsx")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar las guías: {str(e)}")

@app.post("/manual-import/")
async def manual_import(file: UploadFile = File(...), db: Session = Depends(get_session)):
    try:
        import pandas as pd
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

        columnas_requeridas = {'GD', 'Fecha', 'Proveedor', 'TAG', 'Descripcion Material', 'Cantidad'}
        if not columnas_requeridas.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"Faltan columnas requeridas: {', '.join(columnas_requeridas)}")

        for _, row in df.iterrows():
            fecha = datetime.strptime(row["Fecha"], "%Y-%m-%d").date()
            gid = str(row['GD']).strip()
            guia = db.exec(select(Guia).where(Guia.id_guid == gid)).first()
            if not guia:
                guia = Guia(
                    id_guid=gid,
                    fecha=fecha,
                    proveedor=row.get('Proveedor', None)
                )
                db.add(guia)

            item = Item(
                tag=row['TAG'],
                descripcion=row['Descripcion Material'],
                cantidad=int(row['Cantidad']),
                id_guid=gid
            )
            db.add(item)

        db.commit()
        return {"message": f"Importación completada: {len(df)} registros procesados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port)