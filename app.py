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

# --- Inicialização do App ---
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
        raise HTTPException(401, "Token inválido ou expirado")

# ============================
# 🔐 AUTENTICAÇÃO
# ============================

@app.post("/auth/login/")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(400, "Usuário ou senha incorretos")
    token = jwt.encode({"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=8)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# ============================
# 🛠️ ENDPOINTS PARA OS SELECTS (O QUE ESTÁ FALTANDO!)
# ============================

@app.get("/cities/", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)):
    return db.query(models.City).all()

@app.get("/neighborhoods/", response_model=List[schemas.NeighborhoodOut])
def list_neighborhoods(db: Session = Depends(get_db)):
    return db.query(models.Neighborhood).all()

@app.get("/routes/", response_model=List[schemas.RouteOut])
def list_routes(db: Session = Depends(get_db)):
    return db.query(models.Route).all()

@app.get("/vehicles/", response_model=List[schemas.VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(models.Vehicle).all()

# ============================
# 🔗 SALVAR VÍNCULO (TELA DE ATENDIMENTO)
# ============================

@app.post("/route-city-day/")
def create_link(payload: schemas.RouteCityDayBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_link = models.RouteCityDay(**payload.dict())
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link

# ============================
# 🔎 CONSULTA PÚBLICA
# ============================

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(models.City.name.ilike(f"%{query}%")).first()
    if not city: raise HTTPException(404, "Cidade não encontrada")
    
    links = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    return {
        "city": city.name,
        "routes": [{
            "route_name": l.route.name,
            "weekday": l.weekday,
            "vehicle_name": l.vehicle.name if l.vehicle else "Frota"
        } for l in links]
    }
