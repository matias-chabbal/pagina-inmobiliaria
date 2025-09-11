from database import SessionLocal
import models

def check_images():
    db = SessionLocal()
    try:
        propiedades = db.query(models.Propiedad).all()
        for p in propiedades:
            print(f"\nPropiedad: {p.titulo}")
            for img in p.imagenes:
                print(f"Image URL: {img.url}")
    finally:
        db.close()

if __name__ == "__main__":
    check_images()