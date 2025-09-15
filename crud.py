from sqlalchemy.orm import Session
import models
import schemas
from typing import List
from pathlib import Path
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def crear_propiedad(db: Session, propiedad: schemas.PropiedadCreate):
    try:
        db_propiedad = models.Propiedad(**propiedad.dict(exclude={'imagenes'}))
        db.add(db_propiedad)
        db.commit()
        db.refresh(db_propiedad)
        return db_propiedad
    except Exception as e:
        db.rollback()
        raise e

def crear_imagen(db, imagen_url: str, propiedad_id: int):
    imagen = models.ImagenPropiedad(url=imagen_url, propiedad_id=propiedad_id)
    db.add(imagen)
    db.commit()
    db.refresh(imagen)
    return imagen

def listar_propiedades(
    db: Session,
    disponibles: bool = True,
    tipo: str = None,
    operacion: str = None,
    precio_min: float = None,
    precio_max: float = None,
    ubicacion: str = None
):
    query = db.query(models.Propiedad).filter(models.Propiedad.disponible == disponibles)
    if tipo:
        query = query.filter(models.Propiedad.tipo == tipo)
    if operacion:
        query = query.filter(models.Propiedad.operacion == operacion)
    if precio_min:
        query = query.filter(models.Propiedad.precio >= precio_min)
    if precio_max:
        query = query.filter(models.Propiedad.precio <= precio_max)
    if ubicacion:
        query = query.filter(models.Propiedad.ubicacion.ilike(f"%{ubicacion}%"))
    return query.order_by(models.Propiedad.id.desc()).all()

def obtener_propiedad(db: Session, propiedad_id: int):
    return db.query(models.Propiedad)\
             .filter(models.Propiedad.id == propiedad_id)\
             .first()

def delete_propiedad(db: Session, propiedad_id: int):
    try:
        propiedad = db.query(models.Propiedad).filter(models.Propiedad.id == propiedad_id).first()
        if propiedad:
            # Delete associated images from filesystem
            for imagen in propiedad.imagenes:
                filepath = Path("." + imagen.url)
                if filepath.exists():
                    filepath.unlink()
            
            # Delete from database (cascade will handle imagenes_propiedad)
            db.delete(propiedad)
            db.commit()
            return True
    except Exception as e:
        db.rollback()
        raise e
