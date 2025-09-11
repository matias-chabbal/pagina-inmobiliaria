from pathlib import Path
from database import SessionLocal
import models
import shutil

def verify_and_fix_images():
    db = SessionLocal()
    try:
        # Ensure images directory exists
        image_dir = Path("static/images")
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # Check all properties and their images
        propiedades = db.query(models.Propiedad).all()
        for p in propiedades:
            print(f"\nVerificando propiedad {p.id}: {p.titulo}")
            
            for img in p.imagenes:
                # Remove any URL encoding
                clean_url = img.url.replace('%20', ' ')
                
                # Get file path from URL
                file_path = Path("." + clean_url)
                
                print(f"Checking image: {clean_url}")
                
                if not file_path.exists():
                    print(f"❌ File missing: {file_path}")
                    # Remove invalid database entry
                    db.delete(img)
                else:
                    print(f"✅ File exists: {file_path}")
                    # Verify file is actually an image
                    try:
                        with file_path.open('rb') as f:
                            # Read first few bytes to check if it's an image
                            header = f.read(8)
                            if not any(header.startswith(sig) for sig in [b'\xFF\xD8', b'\x89PNG', b'GIF87a', b'GIF89a']):
                                print("❌ Invalid image file")
                                db.delete(img)
                    except Exception as e:
                        print(f"❌ Error checking file: {e}")
                        db.delete(img)
        
        # Commit changes
        db.commit()
        print("\nVerification complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    verify_and_fix_images()