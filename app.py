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

# --- Configurações de Segurança ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_password_hash(password): return pwd_context.hash(password)
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

# --- Inicialização ---
models.Base.metadata.create_all(bind=engine)
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
        if not user: raise HTTPException(401)
        return user
    except:
        raise HTTPException(401, "Sessão expirada. Faça login novamente.")

# ============================
# 🔐 AUTENTICAÇÃO
# ============================

@app.post("/auth/login/")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(400, "Usuário ou senha incorretos")
    
    token = jwt.encode(
        {"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=8)}, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer"}

# ============================
# 🏙️ LISTAGENS (SELECTS)
# ============================

@app.get("/cities/", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)):
    return db.query(models.City).all()

@app.post("/cities/", response_model=schemas.CityOut)
def create_city(city: schemas.CityBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_city = models.City(name=city.name)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

@app.get("/routes/", response_model=List[schemas.RouteOut])
def list_routes(db: Session = Depends(get_db)):
    return db.query(models.Route).all()

@app.get("/vehicles/", response_model=List[schemas.VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(models.Vehicle).all()

# ============================
# 🔗 VÍNCULOS (ATENDIMENTO)
# ============================

@app.get("/route-city-day/")
def list_links(db: Session = Depends(get_db)):
    try:
        links = db.query(models.RouteCityDay).all()
        result = []
        for l in links:
            # Proteção contra objetos deletados (Avoid Error 500)
            result.append({
                "id": l.id,
                "route_id": l.route_id,
                "city_id": l.city_id,
                "weekday": l.weekday,
                "route_name": l.route.name if l.route else "Rota N/A",
                "city_name": l.city.name if l.city else "Cidade N/A",
                "neighborhood_name": getattr(l, 'neighborhood_name', ""),
                "vehicle_name": f"{l.vehicle.name} ({l.vehicle.plate})" if l.vehicle else "Frota"
            })
        return result
    except Exception as e:
        print(f"Erro ao listar: {e}")
        return []

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
        db.refresh(new_link)
        return {"status": "sucesso", "id": new_link.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao salvar vínculo. Verifique os dados.")

@app.delete("/route-city-day/{link_id}/")
def delete_link(link_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db.query(models.RouteCityDay).filter_by(id=link_id).delete()
    db.commit()
    return {"message": "Deletado"}

# ============================
# 🔎 CONSULTA PÚBLICA
# ============================

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(models.City.name.ilike(f"%{query}%")).first()
    if not city:
        raise HTTPException(404, "Cidade não encontrada")
    
    links = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    return {
        "city": city.name,
        "routes": [{
            "route_name": l.route.name if l.route else "Rota s/ nome",
            "weekday": l.weekday,
            "neighborhood_name": l.neighborhood_name or "Geral",
            "vehicle_name": l.vehicle.name if l.vehicle else "Frota"
        } for l in links]
    }
