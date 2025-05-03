import sys
import pandas as pd
from sqlmodel import Session
from models import Guia, Item
from database import engine, init_db
from datetime import datetime
from fastapi import HTTPException

# Inicializar la base de datos
init_db()

# Validar argumentos
if len(sys.argv) < 2:
    print("Uso: python cli_import.py <archivo.xlsx>")
    sys.exit(1)

archivo = sys.argv[1]

try:
    # Leer el archivo Excel
    df = pd.read_excel(archivo)

    # Validar columnas requeridas
    columnas_requeridas = {'GD', 'Fecha', 'Proveedor', 'TAG', 'Descripcion Material', 'Cantidad'}
    if not columnas_requeridas.issubset(df.columns):
        print(f"Error: El archivo debe contener las columnas: {', '.join(columnas_requeridas)}")
        sys.exit(1)

    # Procesar datos e insertar en la base de datos
    with Session(engine) as session:
        for _, row in df.iterrows():
            # Validar fecha
            try:
                fecha = datetime.strptime(row["Fecha"], "%Y-%m-%d")  # Ajusta el formato según tu archivo
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

        # Confirmar todos los cambios en la base de datos
        session.commit()

    print(f"Importación completada: {len(df)} registros procesados.")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo '{archivo}'. Verifica la ruta y vuelve a intentarlo.")
except Exception as e:
    print(f"Error inesperado: {e}")
