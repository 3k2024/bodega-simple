from typing import Optional
from datetime import datetime
import os
import logging
from fastapi import FastAPI, Request, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from db_config import init_db, get_session
from models import Guia, Item
import pandas as pd

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Inicialización de BD y App
init_db()
app = FastAPI(
    title="Bodega Internacional",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#---------pagina web de inicio------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Página de inicio."""
    return templates.TemplateResponse("home.html", {"request": request})

#ingreso de guias manualmente----------------

@app.get("/click_ingreso_guia", response_class=HTMLResponse)
def mostrar_formulario_ingreso_guia(request: Request):
    """Muestra el formulario para ingresar guías manualmente."""
    return templates.TemplateResponse("ingreso_guia.html", {"request": request})

#ingreso de guias manualmente click----------------

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
    """Guarda una guía manualmente junto con sus ítems."""
    try:
        logger.debug(f"Datos recibidos: id_guid={id_guid}, fecha={fecha}, tag={tag}, descripcion={descripcion}, cantidad={cantidad}")
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        guia = db.exec(select(Guia).where(Guia.id_guid == id_guid)).first()
        if not guia:
            logger.debug(f"No se encontró la guía con id_guid={id_guid}. Creando una nueva.")
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
        logger.info(f"Guía e ítem guardados correctamente: id_guid={id_guid}, tag={tag}")
        return {"message": "Guía guardada correctamente."}
    except Exception as e:
        logger.error(f"Error al guardar la guía: {e}")
        raise HTTPException(status_code=500, detail=f"Error al guardar la guía: {str(e)}")



#------------link exportar a excel----------------

@app.get("/export-excel/")
def exportar_guias_a_excel(
    proveedor: Optional[str] = None,
    especialidad: Optional[str] = None,
    db: Session = Depends(get_session)
):
    """Exporta las guías e ítems a un archivo Excel con filtros opcionales."""
    try:
        # Consulta base para obtener las guías
        query = select(Guia)
        if proveedor:
            query = query.where(Guia.proveedor == proveedor)
        guias = db.exec(query).all()

        # Filtrar ítems por especialidad si se proporciona
        data = []
        for guia in guias:
            for item in guia.items:
                if especialidad and item.especialidad != especialidad:
                    continue
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

        # Generar el archivo Excel
        file_path = "guias_exportadas.xlsx"
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="guias_exportadas.xlsx")
    except Exception as e:
        logger.error(f"Error al exportar las guías: {e}")
        raise HTTPException(status_code=500, detail=f"Error al exportar las guías: {str(e)}")

#----------------------exprotar a excel FIN----------------
@app.get("/importar-excel", response_class=HTMLResponse)
def formulario_importar_excel(request: Request):
    """Muestra el formulario para importar guías desde un archivo Excel."""
    return templates.TemplateResponse("importar_excel.html", {"request": request})


#---PROCESAR ARCHIVO EXCEL Y CARGAR A BD----------------


@app.post("/procesar-excel")
async def procesar_excel(file: UploadFile = File(...), db: Session = Depends(get_session)):
    """Procesa un archivo Excel y guarda los datos en la base de datos."""
    try:
        if not file.filename.endswith(".xlsx"):
            raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

        # Leer el archivo Excel
        df = pd.read_excel(file.file)

        # Cabeceras requeridas
        columnas_requeridas = {'GD', 'Fecha', 'Proveedor', 'TAG', 'Descripcion Material', 'Cantidad'}

        # Verificar si las cabeceras requeridas están presentes
        columnas_presentes = set(df.columns)
        if not columnas_requeridas.issubset(columnas_presentes):
            raise HTTPException(
                status_code=400,
                detail=f"Faltan columnas requeridas: {', '.join(columnas_requeridas - columnas_presentes)}"
            )

        # Reordenar las columnas según las cabeceras requeridas
        df = df[list(columnas_requeridas)]

        # Procesar cada fila del archivo
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
        return {"message": "Archivo procesado y datos guardados correctamente."}
    except Exception as e:
        logger.error(f"Error al procesar el archivo Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")