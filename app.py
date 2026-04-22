import os
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

import models, schemas
from database import engine, SessionLocal

# --- Configurações de Segurança ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Inicialização ---
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Sistema de Rotas", version="1.0.0")

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

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None: raise HTTPException(401, "Token inválido")
    except JWTError: raise HTTPException(401, "Token expirado")
    user = db.query(models.User).filter_by(username=username).first()
    if not user: raise HTTPException(401, "Usuário não encontrado")
    return user

# --- Admin Padrão ---
def init_admin_user():
    db = SessionLocal()
    try:
        if not db.query(models.User).filter_by(username="admin").first():
            db.add(models.User(username="admin", hashed_password=get_password_hash("123456"), is_active=True))
            db.commit()
    finally:
        db.close()

init_admin_user()

# ============================
# 🔐 Autenticação
# ============================

@app.post("/auth/login/")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(400, "Credenciais inválidas")
    return {"access_token": create_access_token({"sub": user.username}), "token_type": "bearer"}

# ============================
# 🏙️ Cadastro de Cidades (O que estava dando erro)
# ============================

@app.get("/cities/", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)):
    return db.query(models.City).all()

@app.post("/cities/", response_model=schemas.CityOut)
def create_city(city: schemas.CityCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if db.query(models.City).filter_by(name=city.name).first():
        raise HTTPException(400, "Cidade já existe")
    new_city = models.City(name=city.name, latitude=city.latitude, longitude=city.longitude)
    db.add(new_city)
    db.commit()
    db.refresh(new_city)
    return new_city

# ============================
# 🔎 Consultas Públicas
# ============================

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(models.City.name.ilike(f"%{query}%")).first()
    if not city: raise HTTPException(404, "Nada encontrado")
    routes = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    return {
        "city": city.name,
        "routes": [{
            "route_name": r.route.name,
            "weekday": r.weekday,
            "vehicle_name": r.vehicle.name if r.vehicle else None
        } for r in routes]
    }
