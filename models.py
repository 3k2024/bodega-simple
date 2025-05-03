from enum import Enum as PyEnum
from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import date

class EspecialidadEnum(str, PyEnum):
    ESTRUCTURA             = "Estructura"
    ELECTRICO              = "Eléctrico"
    CIVIL                  = "Civil"
    FIERRO                 = "Fierro"
    VALVULAS               = "Válvulas"
    INSTRUMENTACION        = "Instrumentación"
    MECANICA_EQUIPOS       = "Mecánica Equipos"
    ELECTRICOS_EQUIPOS     = "Eléctricos Equipos"
    CANERIAS               = "Cañerías"

class Guia(SQLModel, table=True):
    id_guid: str = Field(primary_key=True, index=True)
    fecha: date  # Cambiado de str a date para mayor precisión
    proveedor: Optional[str] = None
    observacion: Optional[str] = None

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tag: str
    descripcion: str
    cantidad: int
    especialidad: Optional[EspecialidadEnum] = Field(default=None, nullable=True)
    id_guid: str = Field(foreign_key="guia.id_guid")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str
