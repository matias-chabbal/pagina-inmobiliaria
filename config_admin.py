# Ejecuta esto una vez para crear el admin seguro
from crud import hash_password
from models import Admin
from database import SessionLocal

db = SessionLocal()
admin = Admin(username="admin", password_hash=hash_password("admin123"))
db.add(admin)
db.commit()
db.close()