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

# --- Segurança ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_password_hash(password): return pwd_context.hash(password)
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- App ---
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
    try: yield db
    finally: db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username: raise HTTPException(401, "Token inválido")
    except JWTError: raise HTTPException(401, "Token expirado")
    user = db.query(models.User).filter_by(username=username).first()
    if not user: raise HTTPException(401, "Usuário não encontrado")
    return user

# --- Admin ---
def init_admin_user():
    db = SessionLocal()
    try:
        if not db.query(models.User).filter_by(username="admin").first():
            db.add(models.User(username="admin", hashed_password=get_password_hash("123456"), is_active=True))
            db.commit()
    finally: db.close()

init_admin_user()

# ============================
# 🔐 Auth & 🏙️ Cidades
# ============================

@app.post("/auth/login/")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(400, "Credenciais inválidas")
    return {"access_token": create_access_token({"sub": user.username}), "token_type": "bearer"}

@app.get("/cities/", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)):
    return db.query(models.City).all()

@app.post("/cities/", response_model=schemas.CityOut)
def create_city(city: schemas.CityCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_city = models.City(name=city.name, latitude=city.latitude or 0, longitude=city.longitude or 0)
    db.add(new_city)
    db.commit()
    db.refresh(new_city)
    return new_city

# ============================
# 🏘️ Bairros (Neighborhoods)
# ============================

@app.get("/neighborhoods/", response_model=List[schemas.NeighborhoodOut])
def list_neighborhoods(db: Session = Depends(get_db)):
    return db.query(models.Neighborhood).all()

@app.post("/neighborhoods/", response_model=schemas.NeighborhoodOut)
def create_neighborhood(n: schemas.NeighborhoodCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Aqui o cadastro é independente de rota!
    new_n = models.Neighborhood(
        name=n.name, 
        city_id=n.city_id, 
        latitude=getattr(n, 'latitude', 0), 
        longitude=getattr(n, 'longitude', 0)
    )
    db.add(new_n)
    db.commit()
    db.refresh(new_n)
    return new_n

@app.patch("/neighborhoods/{nb_id}/")
def update_neighborhood(nb_id: int, n: schemas.NeighborhoodCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_nb = db.query(models.Neighborhood).filter_by(id=nb_id).first()
    if not db_nb: raise HTTPException(404, "Bairro não encontrado")
    db_nb.name = n.name
    db_nb.city_id = n.city_id
    db.commit()
    return {"message": "Atualizado"}

# ============================
# 🔎 Consulta Pública
# ============================

@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(models.City.name.ilike(f"%{query}%")).first()
    if not city: raise HTTPException(404, "Cidade não encontrada")
    
    # Busca vínculos na tabela RouteCityDay
    routes = db.query(models.RouteCityDay).filter_by(city_id=city.id).all()
    return {
        "city": city.name,
        "routes": [{
            "route_name": r.route.name,
            "weekday": r.weekday,
            "vehicle_name": r.vehicle.name if r.vehicle else None
        } for r in routes]
    }
