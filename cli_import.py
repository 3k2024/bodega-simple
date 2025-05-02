import sys
import pandas as pd
from sqlmodel import Session
from models import Guia, Item
from database import engine, init_db

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
        for _, r in df.iterrows():
            gid = str(r['GD']).strip()
            guia = session.get(Guia, gid)
            if not guia:
                guia = Guia(
                    id_guid=gid,
                    fecha=str(r['Fecha']),
                    proveedor=r.get('Proveedor', None)
                )
                session.add(guia)

            item = Item(
                tag=r['TAG'],
                descripcion=r['Descripcion Material'],
                cantidad=int(r['Cantidad']),
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
