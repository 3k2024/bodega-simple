from enum import Enum as PyEnum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
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
    id_guid: str = Field(primary_key=True)
    fecha: date  # Asegúrate de que sea de tipo date
    proveedor: Optional[str] = None
    observacion: Optional[str] = None

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tag: str
    descripcion: str
    cantidad: int
    especialidad: Optional[EspecialidadEnum] = Field(default=None, nullable=True)
    id_guid: str = Field(foreign_key="guia.id_guid")
    guia: Optional[Guia] = Relationship(back_populates="items")  # Relación con la guía

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str
