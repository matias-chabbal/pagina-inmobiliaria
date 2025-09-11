from database import SessionLocal
import models

def test_crear_propiedad():
    db = SessionLocal()
    try:
        # Crear propiedad
        propiedad = models.Propiedad(
            titulo="Casa de Prueba",
            descripcion="Una hermosa casa para pruebas",
            precio=150000,
            tipo="Casa",
            disponible=True,
            ubicacion="Calle Principal 123",
            ubicacion_maps="https://maps.google.com/?q=..."
        )
        db.add(propiedad)
        db.commit()
        
        # Agregar imagen
        imagen = models.ImagenPropiedad(
            url="/static/images/test-house.jpg",
            propiedad_id=propiedad.id
        )
        db.add(imagen)
        db.commit()
        
        print("Propiedad creada exitosamente")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_crear_propiedad()