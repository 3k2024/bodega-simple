from typing import Optional, List
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tag: str
    descripcion: str
    cantidad: int
    especialidad: Optional[str] = None
    id_guid: str = Field(foreign_key="guia.id_guid")
    guia: Optional["Guia"] = Relationship(back_populates="items")  # Relación con Guia

class Guia(SQLModel, table=True):
    id_guid: str = Field(primary_key=True)
    fecha: date
    proveedor: Optional[str] = None
    observacion: Optional[str] = None
    items: List[Item] = Relationship(back_populates="guia")  # Relación con Item