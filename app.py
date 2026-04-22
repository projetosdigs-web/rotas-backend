import os
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import engine, SessionLocal
from sqlalchemy import text

# Inicialização
models.Base.metadata.create_all(bind=engine)

# Garante que a coluna de texto para bairro existe
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE route_city_day ADD COLUMN IF NOT EXISTS neighborhood_name VARCHAR"))
        conn.commit()
    except Exception: pass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporário para testes, depois volte a URL da Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- Endpoints de Listagem ---

@app.get("/cities/")
def list_cities(db: Session = Depends(get_db)):
    return db.query(models.City).all()

@app.get("/routes/")
def list_routes(db: Session = Depends(get_db)):
    return db.query(models.Route).all()

@app.get("/vehicles/")
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(models.Vehicle).all()

@app.get("/route-city-day/")
def list_links(db: Session = Depends(get_db)):
    links = db.query(models.RouteCityDay).all()
    return [{
        "id": l.id,
        "route_name": l.route.name if l.route else "N/A",
        "city_name": l.city.name if l.city else "N/A",
        "neighborhood_name": l.neighborhood_name or "Geral",
        "weekday": l.weekday
    } for l in links]

# (Mantenha aqui as rotas de POST e LOGIN que já funcionam)
