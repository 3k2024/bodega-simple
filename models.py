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
    fecha: date
    proveedor: Optional[str] = None
    observacion: Optional[str] = None

    # Relación con el modelo Item
    items: List["Item"] = Relationship(back_populates="guia")

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tag: str
    descripcion: str
    cantidad: int
    especialidad: Optional[str] = None
    id_guid: str = Field(foreign_key="guia.id_guid")

    # Relación inversa con el modelo Guia
    guia: Optional[Guia] = Relationship(back_populates="items")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str