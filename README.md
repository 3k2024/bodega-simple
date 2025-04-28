# Bodega Simple

## Uso rápido

```bash
# 1. Crea un entorno virtual e instala dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Arranca la API
uvicorn main:app --reload
# Abre http://localhost:8000/docs en tu navegador

# 3. (opcional) Importa tu Excel
python cli_import.py /ruta/a/tu_archivo.xlsx
```
