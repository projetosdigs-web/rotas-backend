import os
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
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

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

# --- Inicialização ---
models.Base.metadata.create_all(bind=engine)

# Garantir usuário admin
with SessionLocal() as db_setup:
    try:
        admin = db_setup.query(models.User).filter_by(username="admin").first()
        if not admin:
            db_setup.add(models.User(username="admin", hashed_password=pwd_context.hash("123456")))
            db_setup.commit()
    except: pass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rotas-frontend-alpha.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- Rotas de Autenticação ---
@app.post("/auth/login/")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(400, "Dados incorretos")
    token = jwt.encode({"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=8)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# --- Rotas de Gerenciamento (Onde corrigimos o 405) ---

@app.get("/routes/", response_model=List[schemas.RouteOut])
def list_routes(db: Session = Depends(get_db)): return db.query(models.Route).all()

@app.post("/routes/") # ESTA ROTA É A QUE ESTAVA DANDO ERRO 405
def create_route(payload: dict = Body(...), db: Session = Depends(get_db)):
    new_route = models.Route(name=payload.get("name"), description=payload.get("description", ""))
    db.add(new_route)
    db.commit()
    db.refresh(new_route)
    return new_route

@app.get("/cities/", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)): return db.query(models.City).all()

@app.post("/cities/")
def create_city(payload: dict = Body(...), db: Session = Depends(get_db)):
    new_city = models.City(name=payload.get("name"), latitude=payload.get("latitude"), longitude=payload.get("longitude"))
    db.add(new_city)
    db.commit()
    db.refresh(new_city)
    return new_city

@app.get("/route-city-day/")
def list_links(db: Session = Depends(get_db)):
    links = db.query(models.RouteCityDay).all()
    return [{"id": l.id, "route_id": l.route_id, "city_id": l.city_id, "weekday": l.weekday, 
             "route_name": l.route.name if l.route else "N/A", "city_name": l.city.name if l.city else "N/A",
             "neighborhood_name": getattr(l, "neighborhood_name", ""),
             "vehicle_name": l.vehicle.name if l.vehicle else "Frota"} for l in links]

@app.post("/route-city-day/")
def create_link(payload: dict = Body(...), db: Session = Depends(get_db)):
    new_link = models.RouteCityDay(
        route_id=payload.get("route_id"), city_id=payload.get("city_id"),
        weekday=payload.get("weekday"), vehicle_id=payload.get("vehicle_id"),
        neighborhood_name=payload.get("neighborhood_name", "")
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(models.City.name.ilike(f"%{query}%")).first()
    if not city: raise HTTPException(404)
    links = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    return {"city": city.name, "routes": [{"route_name": l.route.name if l.route else "N/A", "weekday": l.weekday, "neighborhood_name": getattr(l, "neighborhood_name", ""), "latitude": city.latitude, "longitude": city.longitude} for l in links]}
