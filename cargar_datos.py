import requests
import random
from datetime import datetime, timedelta

# URL base de la aplicación FastAPI
BASE_URL = "https://bodega-simple.onrender.com"

# Función para cargar una guía manualmente
def cargar_guia_manual(id_guid, fecha, tag, descripcion, cantidad, proveedor=None, observacion=None, especialidad=None):
    url = f"{BASE_URL}/click_ingreso_guia"
    data = {
        "id_guid": id_guid,
        "fecha": fecha,
        "tag": tag,
        "descripcion": descripcion,
        "cantidad": cantidad,
        "proveedor": proveedor,
        "observacion": observacion,
        "especialidad": especialidad,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print(f"Guía {id_guid} cargada correctamente: {response.json()}")
    else:
        print(f"Error al cargar la guía {id_guid}: {response.status_code} - {response.text}")

# Generar datos aleatorios para las guías
def generar_datos_aleatorios():
    guias = []
    for i in range(5):  # Generar 5 guías aleatorias
        id_guid = f"G{random.randint(100, 999)}"
        fecha = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        tag = f"T{random.randint(1000, 9999)}"
        descripcion = f"Descripción del ítem {i + 1}"
        cantidad = random.randint(1, 100)
        proveedor = f"Proveedor {chr(65 + i)}"
        observacion = f"Observación {i + 1}"
        especialidad = random.choice(["General", "Especialidad A", "Especialidad B"])
        guias.append((id_guid, fecha, tag, descripcion, cantidad, proveedor, observacion, especialidad))
    return guias

# Función principal para ejecutar las pruebas
def main():
    print("Cargando guías con datos aleatorios...")
    guias = generar_datos_aleatorios()
    for guia in guias:
        cargar_guia_manual(*guia)

if __name__ == "__main__":
    main()