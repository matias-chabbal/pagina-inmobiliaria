from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
def mostrar_propiedades(request: Request, db: Session = Depends(get_db)):
    propiedades = crud.listar_propiedades(db)
    print(f"Número de propiedades encontradas: {len(propiedades)}")  # Debug
    return templates.TemplateResponse(
        "public.html", 
        {"request": request, "propiedades": propiedades}
    )

@router.get("/propiedad/{id}", response_class=HTMLResponse)
def mostrar_propiedad(request: Request, id: int, db: Session = Depends(get_db)):
    propiedad = crud.obtener_propiedad(db, id)
    if not propiedad:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        "propiedad_detalle.html", 
        {"request": request, "propiedad": propiedad}
    )

@router.get("/sobre-nosotros", response_class=HTMLResponse)
async def sobre_nosotros(request: Request):
    # Get list of images from the about folder
    about_images_dir = Path("static/images/about")
    about_images_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
    
    # Get all image files with common extensions
    about_images = []
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        about_images.extend(about_images_dir.glob(f'*{ext}'))
    
    # Convert Path objects to strings and get just the filenames
    image_names = [img.name for img in about_images]
    
    return templates.TemplateResponse(
        "sobre_nosotros.html",
        {"request": request, "imagenes": image_names}
    )
