from sqlalchemy.orm import Session
import models
import schemas
from typing import List
from pathlib import Path

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

def crear_imagen(db: Session, imagen_url: str, propiedad_id: int):
    try:
        db_imagen = models.ImagenPropiedad(url=imagen_url, propiedad_id=propiedad_id)
        db.add(db_imagen)
        db.commit()
        db.refresh(db_imagen)
        return db_imagen
    except Exception as e:
        db.rollback()
        raise e

def listar_propiedades(db: Session, disponibles: bool = True):
    return db.query(models.Propiedad)\
             .filter(models.Propiedad.disponible == disponibles)\
             .order_by(models.Propiedad.id.desc())\
             .all()

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
