import os
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import engine, SessionLocal
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import text

# --- Segurança ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

# --- Inicialização do Banco ---
models.Base.metadata.create_all(bind=engine)

# GARANTIR QUE O USUÁRIO ADMIN EXISTA (Para você conseguir logar)
with SessionLocal() as db_setup:
    try:
        admin_user = db_setup.query(models.User).filter_by(username="admin").first()
        if not admin_user:
            hashed_pw = pwd_context.hash("123456")
            new_admin = models.User(username="admin", hashed_password=hashed_pw)
            db_setup.add(new_admin)
            db_setup.commit()
            print("Usuário admin padrão criado: admin / 123456")
    except Exception as e:
        print(f"Erro ao criar admin: {e}")

# Forçar criação da coluna de bairro se ela sumiu
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE route_city_day ADD COLUMN IF NOT EXISTS neighborhood_name VARCHAR"))
        conn.commit()
    except Exception: pass

app = FastAPI(title="Ferperez RotaCerta")

# --- Configuração de CORS (Essencial para Vercel) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rotas-frontend-alpha.vercel.app", 
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# ============================
# 🔐 AUTH & LISTAGENS GERAIS
# ============================

@app.post("/auth/login/")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(400, "Dados incorretos")
    
    token = jwt.encode(
        {"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=8)}, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/cities/", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)): return db.query(models.City).all()

@app.get("/routes/", response_model=List[schemas.RouteOut])
def list_routes(db: Session = Depends(get_db)): return db.query(models.Route).all()

@app.get("/vehicles/", response_model=List[schemas.VehicleOut])
def list_vehicles(db: Session = Depends(get_db)): return db.query(models.Vehicle).all()

# ============================
# 🔗 VÍNCULOS
# ============================

@app.get("/route-city-day/")
def list_links(db: Session = Depends(get_db)):
    try:
        links = db.query(models.RouteCityDay).all()
        return [{
            "id": l.id,
            "route_id": l.route_id,
            "city_id": l.city_id,
            "weekday": l.weekday,
            "route_name": l.route.name if l.route else "N/A",
            "city_name": l.city.name if l.city else "N/A",
            "neighborhood_name": getattr(l, "neighborhood_name", ""),
            "vehicle_name": l.vehicle.name if l.vehicle else "Frota"
        } for l in links]
    except Exception: return []

@app.post("/route-city-day/")
def create_link(payload: dict = Body(...), db: Session = Depends(get_db)):
    new_link = models.RouteCityDay(
        route_id=payload.get("route_id"),
        vehicle_id=payload.get("vehicle_id"),
        city_id=payload.get("city_id"),
        weekday=payload.get("weekday"),
        neighborhood_name=payload.get("neighborhood_name", "")
    )
    db.add(new_link)
    db.commit()
    return {"status": "ok"}

@app.delete("/route-city-day/{id}/")
def delete_link(id: int, db: Session = Depends(get_db)):
    db.query(models.RouteCityDay).filter_by(id=id).delete()
    db.commit()
    return {"status": "ok"}

# ============================
# 🔎 CONSULTA (VENDEDORES)
# ============================

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(models.City.name.ilike(f"%{query}%")).first()
    if not city: raise HTTPException(404)
    
    links = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    
    return {
        "city": city.name,
        "routes": [
            {
                "route_name": l.route.name if l.route else "N/A", 
                "weekday": l.weekday, 
                "neighborhood_name": getattr(l, "neighborhood_name", "")
            } for l in links
        ]
    }
