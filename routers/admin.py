from typing import List
from fastapi import APIRouter, Depends, Request, Form, Response, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from database import SessionLocal
import crud, schemas
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from admin_config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils import clean_filename
import uuid
from pathlib import Path
import shutil
import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_logged") != "true":
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    propiedades = crud.listar_propiedades(db)
    return templates.TemplateResponse(
        "admin.html", 
        {"request": request, "propiedades": propiedades}
    )

@router.post("/admin/agregar")
async def agregar_propiedad(
    request: Request,
    titulo: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    tipo: str = Form(...),
    imagenes: List[UploadFile] = File(...),
    ubicacion: str = Form(...),
    ubicacion_maps: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Create property
        propiedad_data = schemas.PropiedadCreate(
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
            tipo=tipo,
            ubicacion=ubicacion,
            ubicacion_maps=ubicacion_maps,
            disponible=True
        )
        
        propiedad = crud.crear_propiedad(db, propiedad_data)
        
        # Process images
        UPLOAD_DIR = Path("static/images")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        for imagen in imagenes:
            try:
                # Get file content
                content = await imagen.read()
                
                # Create a simple unique filename with extension
                ext = ".png" if imagen.content_type == "image/png" else ".jpg"
                unique_filename = f"{uuid.uuid4()}{ext}"
                
                # Create filepath
                filepath = UPLOAD_DIR / unique_filename
                
                # Save file using binary write mode
                with open(filepath, "wb") as f:
                    f.write(content)
                
                # Create clean URL
                imagen_url = f"/static/images/{unique_filename}"
                crud.crear_imagen(db, imagen_url, propiedad.id)
                
                print(f"Imagen guardada: {imagen_url}")
                
            except Exception as img_error:
                print(f"Error guardando imagen: {str(img_error)}")
                continue
        
        return RedirectResponse(url="/admin", status_code=302)
        
    except Exception as e:
        print(f"Error general: {str(e)}")
        db.rollback()
        raise

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin", status_code=HTTP_302_FOUND)
        response.set_cookie(key="admin_logged", value="true", httponly=True)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})

@router.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    response.delete_cookie("admin_logged")
    return response

def admin_auth(request: Request):
    if request.cookies.get("admin_logged") != "true":
        return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)

@router.post("/admin/delete/{propiedad_id}")
async def delete_propiedad(
    propiedad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Get property and delete
        crud.delete_propiedad(db, propiedad_id)
        return RedirectResponse(url="/admin", status_code=HTTP_302_FOUND)
    except Exception as e:
        print(f"Error deleting property: {str(e)}")
        raise

@router.get("/admin/edit/{prop_id}")
def edit_propiedad_form(request: Request, prop_id: int):
    db: Session = SessionLocal()
    propiedad = db.query(models.Propiedad).filter(models.Propiedad.id == prop_id).first()
    return templates.TemplateResponse("admin_edit.html", {"request": request, "propiedad": propiedad})

@router.post("/admin/edit/{prop_id}")
async def edit_propiedad(
    prop_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    tipo: str = Form(...),
    ubicacion: str = Form(...),
    ubicacion_maps: str = Form(...),
    imagenes: list[UploadFile] = File(None)
):
    db: Session = SessionLocal()
    propiedad = db.query(models.Propiedad).filter(models.Propiedad.id == prop_id).first()
    if propiedad:
        propiedad.titulo = titulo
        propiedad.descripcion = descripcion
        propiedad.precio = precio
        propiedad.tipo = tipo
        propiedad.ubicacion = ubicacion
        propiedad.ubicacion_maps = ubicacion_maps

        # Guardar nuevas imágenes
        if imagenes:
            UPLOAD_DIR = Path("static/images")
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            for imagen in imagenes:
                if imagen.filename:
                    content = await imagen.read()
                    ext = Path(imagen.filename).suffix or ".jpg"
                    unique_filename = f"{uuid.uuid4()}{ext}"
                    filepath = UPLOAD_DIR / unique_filename
                    with open(filepath, "wb") as f:
                        f.write(content)
                    imagen_url = f"/static/images/{unique_filename}"
                    db_imagen = models.ImagenPropiedad(url=imagen_url, propiedad_id=propiedad.id)
                    db.add(db_imagen)
        db.commit()
    return RedirectResponse("/admin?msg=edicion_exitosa", status_code=303)

@router.post("/admin/delete-image/{image_id}")
def delete_image(image_id: int):
    db: Session = SessionLocal()
    imagen = db.query(models.ImagenPropiedad).filter(models.ImagenPropiedad.id == image_id).first()
    if imagen:
        # Elimina el archivo físico
        filepath = Path("." + imagen.url)
        if filepath.exists():
            filepath.unlink()
        propiedad_id = imagen.propiedad_id
        db.delete(imagen)
        db.commit()
        # Redirige de vuelta a la edición de la propiedad
        return RedirectResponse(f"/admin/edit/{propiedad_id}", status_code=303)
    # Si no existe, redirige al admin
    return RedirectResponse("/admin", status_code=303)
