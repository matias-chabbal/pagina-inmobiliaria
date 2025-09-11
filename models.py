from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Propiedad(Base):
    __tablename__ = "propiedad"  # O el nombre real de tu tabla
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    precio = Column(Float, nullable=False)
    tipo = Column(String(50), nullable=False)
    disponible = Column(Boolean, default=True)
    ubicacion = Column(String(200), nullable=False)
    ubicacion_maps = Column(String(500), nullable=True)
    operacion = Column(String, default="venta")  # Puede ser "venta" o "alquiler"
    
    # Define the relationship with cascade delete
    imagenes = relationship("ImagenPropiedad", 
                          back_populates="propiedad", 
                          cascade="all, delete-orphan")

class ImagenPropiedad(Base):
    __tablename__ = "imagenes_propiedad"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    propiedad_id = Column(Integer, ForeignKey("propiedad.id", ondelete="CASCADE"), nullable=False)
    
    propiedad = relationship("Propiedad", back_populates="imagenes")
