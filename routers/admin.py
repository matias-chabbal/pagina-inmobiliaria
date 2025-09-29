from typing import List
from fastapi import APIRouter, Depends, Request, Form, Response, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from database import SessionLocal
import crud, schemas
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

from utils import clean_filename
import uuid
from pathlib import Path
import shutil
import models
from crud import listar_propiedades, crear_imagen, crear_propiedad, crear_imagen
from crud import verify_password
from models import Admin
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
def public_home(request: Request):
    db: Session = SessionLocal()
    tipo = request.query_params.get("tipo")
    operacion = request.query_params.get("operacion")
    precio_min = request.query_params.get("precio_min")
    precio_max = request.query_params.get("precio_max")
    ubicacion = request.query_params.get("ubicacion")

    propiedades = listar_propiedades(
        db,
        disponibles=True,
        tipo=tipo,
        operacion=operacion,
        precio_min=float(precio_min) if precio_min else None,
        precio_max=float(precio_max) if precio_max else None,
        ubicacion=ubicacion
    )
    return templates.TemplateResponse("public.html", {"request": request, "propiedades": propiedades})


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
    titulo: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    tipo: str = Form(...),
    disponible: str = Form(...),
    ubicacion: str = Form(...),
    ubicacion_maps: str = Form(...),
    operacion: str = Form(...),
    imagenes: List[UploadFile] = File(None)
):
    db: Session = SessionLocal()
    nueva_propiedad = schemas.PropiedadCreate(
        titulo=titulo,
        descripcion=descripcion,
        precio=precio,
        tipo=tipo,
        disponible=disponible == "on" or disponible == "true",
        ubicacion=ubicacion,
        ubicacion_maps=ubicacion_maps,
        operacion=operacion,
        imagenes=[]
    )
    propiedad = crear_propiedad(db, nueva_propiedad)

    # Guardar imágenes en disco y en la base de datos
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
                crear_imagen(db, imagen_url, propiedad.id)  # <-- Aquí se guarda en la base

    return RedirectResponse("/admin", status_code=303)

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db: Session = SessionLocal()
    admin = autenticar_admin(db, username, password)
    if admin:
        expires = datetime.utcnow() + timedelta(minutes=20)
        response = RedirectResponse(url="/admin", status_code=HTTP_302_FOUND)
        response.set_cookie(
            key="admin_logged",
            value="true",
            httponly=True,
            expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            max_age=20*60,  # 20 minutos en segundos
            samesite="lax"
        )
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})

@router.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    response.delete_cookie("admin_logged")
    return response

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

def admin_auth(request: Request):
    if request.cookies.get("admin_logged") != "true":
        return RedirectResponse(url="/login", status_code=302)

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
    operacion: str = Form(...),
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
        propiedad.operacion = operacion

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
                    # Guarda la imagen en la base de datos
                    crear_imagen(db, imagen_url, propiedad.id)
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

def autenticar_admin(db, username, password):
    admin = db.query(Admin).filter_by(username=username).first()
    if admin and verify_password(password, admin.password_hash):
        return admin
    return None
