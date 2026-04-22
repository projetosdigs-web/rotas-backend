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
from sqlalchemy import text # Importante para a correção

# --- Configurações ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

# --- Inicialização com Correção de Tabela ---
models.Base.metadata.create_all(bind=engine)

# FORÇAR A COLUNA NOVA CASO ELA NÃO EXISTA (CORREÇÃO DO ERRO 500)
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE route_city_day ADD COLUMN IF NOT EXISTS neighborhood_name VARCHAR"))
        conn.commit()
    except Exception as e:
        print(f"Aviso: Coluna já existe ou erro ao criar: {e}")

app = FastAPI(title="Ferperez RotaCerta")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rotas-web-omega.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(models.User).filter_by(username=payload.get("sub")).first()
        return user
    except: raise HTTPException(401, "Sessão expirada")

# ============================
# 🔐 LOGIN & LISTAGENS
# ============================

@app.post("/auth/login/")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(400, "Incorreto")
    token = jwt.encode({"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=8)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/cities/")
def list_cities(db: Session = Depends(get_db)): return db.query(models.City).all()

@app.get("/routes/")
def list_routes(db: Session = Depends(get_db)): return db.query(models.Route).all()

@app.get("/vehicles/")
def list_vehicles(db: Session = Depends(get_db)): return db.query(models.Vehicle).all()

# ============================
# 🔗 VÍNCULOS (CORREÇÃO DO ERRO 500)
# ============================

@app.get("/route-city-day/")
def list_links(db: Session = Depends(get_db)):
    links = db.query(models.RouteCityDay).all()
    res = []
    for l in links:
        res.append({
            "id": l.id,
            "route_id": l.route_id,
            "city_id": l.city_id,
            "weekday": l.weekday,
            "route_name": l.route.name if l.route else "N/A",
            "city_name": l.city.name if l.city else "N/A",
            "neighborhood_name": getattr(l, "neighborhood_name", ""),
            "vehicle_name": l.vehicle.name if l.vehicle else "Frota"
        })
    return res

@app.post("/route-city-day/")
def create_link(payload: dict = Body(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
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
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar: {e}")
        raise HTTPException(500, detail=str(e))

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(models.City.name.ilike(f"%{query}%")).first()
    if not city: raise HTTPException(404)
    links = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    return {
        "city": city.name,
        "routes": [{"route_name": l.route.name, "weekday": l.weekday, "neighborhood_name": l.neighborhood_name} for l in links]
    }
