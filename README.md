# Bodega Simple

## Descripción
Bodega Simple es una aplicación para gestionar guías y artículos en una bodega. Incluye una API construida con FastAPI y soporte para importar datos desde archivos Excel.

## Requisitos
- Python 3.8 o superior
- SQLite (por defecto) o cualquier base de datos compatible con SQLModel
- Dependencias listadas en `requirements.txt`

## Instalación

```bash
# 1. Crea un entorno virtual e instala dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración
Asegúrate de configurar las siguientes variables de entorno antes de ejecutar la aplicación:
- `DATABASE_URL`: URL de conexión a la base de datos (por defecto: `sqlite:///./bodega.db`).
- `SECRET_KEY`: Clave secreta para firmar tokens JWT.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración de los tokens (en minutos).

Puedes usar un archivo `.env` para configurar estas variables.

## Uso rápido

```bash
# 1. Arranca la API
uvicorn main:app --reload
# Abre http://localhost:8000/docs en tu navegador para explorar la API

# 2. (opcional) Importa tu Excel
python cli_import.py /ruta/a/tu_archivo.xlsx
```

## Formato del archivo Excel
El archivo Excel debe contener las siguientes columnas:
- `GD`: Identificador de la guía.
- `Fecha`: Fecha de la guía (formato YYYY-MM-DD).
- `Proveedor`: Nombre del proveedor.
- `TAG`: Identificador del artículo.
- `Descripcion Material`: Descripción del artículo.
- `Cantidad`: Cantidad del artículo.

## Modelos principales
### Guia
- `id_guid`: Identificador único de la guía.
- `fecha`: Fecha de la guía.
- `proveedor`: Nombre del proveedor.
- `observacion`: Observaciones adicionales (opcional).

### Item
- `id`: Identificador único del artículo.
- `tag`: Identificador del artículo.
- `descripcion`: Descripción del artículo.
- `cantidad`: Cantidad del artículo.
- `especialidad`: Especialidad del artículo (opcional).
- `id_guid`: Relación con la guía correspondiente.

### User
- `id`: Identificador único del usuario.
- `username`: Nombre de usuario.
- `hashed_password`: Contraseña encriptada.
- `role`: Rol del usuario (`admin` o `user`).

## Producción
Para ejecutar la aplicación en un entorno de producción, considera usar Gunicorn con Uvicorn:
```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app
```

## Contribución
Si deseas contribuir al proyecto, por favor abre un issue o envía un pull request.

## Licencia
Este proyecto está bajo la licencia MIT.
