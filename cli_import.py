import sys, pandas as pd
from sqlmodel import Session
from models import Guia, Item
from database import engine, init_db

init_db()

if len(sys.argv) < 2:
    print("Uso: python cli_import.py <archivo.xlsx>")
    sys.exit(1)

df = pd.read_excel(sys.argv[1])

with Session(engine) as session:
    for _, r in df.iterrows():
        gid = str(r['GD']).strip()
        guia = session.get(Guia, gid)
        if not guia:
            guia = Guia(id_guid=gid, fecha=str(r['Fecha']), proveedor=r.get('Proveedor', None))
            session.add(guia)
            session.commit()
        item = Item(tag=r['TAG'], descripcion=r['Descripcion Material'], cantidad=int(r['Cantidad']), id_guid=gid)
        session.add(item)
    session.commit()
print("Importación completada")
