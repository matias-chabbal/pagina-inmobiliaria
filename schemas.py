from pydantic import BaseModel
from typing import List

class ImagenCreate(BaseModel):
    url: str

class PropiedadCreate(BaseModel):
    titulo: str
    descripcion: str
    precio: float
    tipo: str
    disponible: bool = True
    ubicacion: str
    ubicacion_maps: str

class Imagen(ImagenCreate):
    id: int
    propiedad_id: int

class Propiedad(PropiedadCreate):
    id: int
    imagenes: List[Imagen] = []

    class Config:
        from_attributes = True
