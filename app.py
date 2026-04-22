import os
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import engine, SessionLocal

# Inicialização do banco
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Sistema de Rotas", version="1.0.0")

# Configuração de CORS para aceitar o domínio do Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rotas-web-omega.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    # 1. Tenta achar como Bairro
    nb = db.query(models.Neighborhood).filter(
        models.Neighborhood.name.ilike(f"%{query}%")).first()
    
    if nb:
        routes = db.query(models.RouteCityDay).filter_by(neighborhood_id=nb.id).all()
        return {
            "city": nb.city.name,
            "city_type": "Bairro",
            "routes": [{
                "route_name": r.route.name,
                "neighborhood_name": nb.name,
                "weekday": r.weekday,
                "vehicle_name": r.vehicle.name if r.vehicle else None,
                "vehicle_plate": r.vehicle.plate if r.vehicle else None,
                "latitude": nb.latitude,
                "longitude": nb.longitude
            } for r in routes]
        }

    # 2. Tenta achar como Cidade
    city = db.query(models.City).filter(
        models.City.name.ilike(f"%{query}%")).first()
    
    if not city:
        raise HTTPException(404, "Nada encontrado")

    routes = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    return {
        "city": city.name,
        "city_type": "Cidade",
        "routes": [{
            "route_name": r.route.name,
            "neighborhood_name": r.neighborhood.name if r.neighborhood else None,
            "weekday": r.weekday,
            "vehicle_name": r.vehicle.name if r.vehicle else None,
            "vehicle_plate": r.vehicle.plate if r.vehicle else None,
            "latitude": r.neighborhood.latitude if r.neighborhood else city.latitude,
            "longitude": r.neighborhood.longitude if r.neighborhood else city.longitude
        } for r in routes]
    }
