from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Propiedad(Base):
    __tablename__ = "propiedades"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float, nullable=False)
    tipo = Column(String(50))
    disponible = Column(Boolean, default=True)
    ubicacion = Column(String(200))
    ubicacion_maps = Column(String(500))
    
    # Define the relationship with cascade delete
    imagenes = relationship("ImagenPropiedad", 
                          back_populates="propiedad", 
                          cascade="all, delete-orphan")

class ImagenPropiedad(Base):
    __tablename__ = "imagenes_propiedad"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id", ondelete="CASCADE"), nullable=False)
    
    propiedad = relationship("Propiedad", back_populates="imagenes")
