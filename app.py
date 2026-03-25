import socket
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, timedelta

import httpx
from jose import JWTError, jwt

import models
import schemas
from database import engine, SessionLocal
from passlib.context import CryptContext

# ============================
# 🔐 Configuração
# ============================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas de duração

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__vary_rounds=0,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================
# ⚙️ Banco de dados
# ============================
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Rotas", version="1.0.0")

security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================
# 🌐 CORS (MODO REDE ABERTA)
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*",  # Permite acesso de qualquer IP na rede
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# 🛠️ Função Auxiliar: Mostrar IP
# ============================


def print_ip_address():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        print(f"\n{'='*60}")
        print(f"🚀 MODO REDE ATIVADO!")
        print(f"📡 Backend rodando. IP da máquina: {ip_address}")
        print(f"{'='*60}\n")
    except:
        pass


print_ip_address()

# ============================
# 👤 Autenticação (Proteção)
# ============================


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado")

    user = db.query(models.User).filter(
        models.User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


def init_admin_user():
    db = SessionLocal()
    try:
        if not db.query(models.User).filter_by(username="admin").first():
            print("Criando admin padrão...")
            db.add(models.User(username="admin",
                   hashed_password=get_password_hash("123456"), is_active=True))
            db.commit()
    finally:
        db.close()


init_admin_user()

# ============================
# 🔐 Endpoints de Auth
# ============================


@app.post("/auth/login")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(
        username=payload.get("username")).first()
    if not user or not verify_password(payload.get("password"), user.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciais inválidas")

    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer"
    }


@app.get("/auth/me")
def read_me(current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username}

# ============================
# 🛣️ CRUDs (Protegidos com current_user)
# ============================


@app.post("/routes/", response_model=schemas.RouteOut)
def create_route(route: schemas.RouteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if db.query(models.Route).filter_by(name=route.name).first():
        raise HTTPException(status_code=400, detail="Rota já existe")
    new_route = models.Route(name=route.name, description=route.description)
    db.add(new_route)
    db.commit()
    db.refresh(new_route)
    return new_route


@app.get("/routes/", response_model=List[schemas.RouteOut])
def list_routes(db: Session = Depends(get_db)):
    return db.query(models.Route).all()


@app.delete("/routes/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    route = db.query(models.Route).filter_by(id=route_id).first()
    if not route:
        raise HTTPException(404, "Rota não encontrada")
    if db.query(models.RouteCityDay).filter_by(route_id=route_id).first():
        raise HTTPException(400, "Remova os vínculos antes.")
    db.delete(route)
    db.commit()
    return {"message": "OK"}


@app.post("/cities/", response_model=schemas.CityOut)
def create_city(city: schemas.CityCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if db.query(models.City).filter_by(name=city.name).first():
        raise HTTPException(400, "Cidade já existe")
    new_city = models.City(
        name=city.name, latitude=city.latitude, longitude=city.longitude)
    db.add(new_city)
    db.commit()
    db.refresh(new_city)
    return new_city


@app.get("/cities/", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)):
    return db.query(models.City).all()


@app.delete("/cities/{city_id}")
def delete_city(city_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    city = db.query(models.City).filter_by(id=city_id).first()
    if not city:
        raise HTTPException(404, "Cidade não encontrada")
    if db.query(models.RouteCityDay).filter_by(city_id=city_id).first():
        raise HTTPException(400, "Remova os vínculos antes.")
    if db.query(models.Neighborhood).filter_by(city_id=city_id).first():
        raise HTTPException(400, "Remova os bairros antes.")
    db.delete(city)
    db.commit()
    return {"message": "OK"}


@app.post("/neighborhoods/", response_model=schemas.NeighborhoodOut)
def create_neighborhood(n: schemas.NeighborhoodCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if db.query(models.Neighborhood).filter_by(name=n.name, city_id=n.city_id).first():
        raise HTTPException(400, "Bairro já existe")
    new_n = models.Neighborhood(
        name=n.name, city_id=n.city_id, latitude=n.latitude, longitude=n.longitude)
    db.add(new_n)
    db.commit()
    db.refresh(new_n)
    return new_n


@app.get("/neighborhoods/", response_model=List[schemas.NeighborhoodOut])
def list_neighborhoods(db: Session = Depends(get_db)):
    return db.query(models.Neighborhood).all()


@app.delete("/neighborhoods/{nb_id}")
def delete_neighborhood(nb_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    nb = db.query(models.Neighborhood).filter_by(id=nb_id).first()
    if not nb:
        raise HTTPException(404, "Bairro não encontrado")
    if db.query(models.RouteCityDay).filter_by(neighborhood_id=nb_id).first():
        raise HTTPException(400, "Remova vínculos antes.")
    db.delete(nb)
    db.commit()
    return {"message": "OK"}


@app.post("/vehicles/", response_model=schemas.VehicleOut)
def create_vehicle(v: schemas.VehicleCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_v = models.Vehicle(name=v.name, plate=v.plate, active=v.active)
    db.add(new_v)
    db.commit()
    db.refresh(new_v)
    return new_v


@app.get("/vehicles/", response_model=List[schemas.VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(models.Vehicle).all()


@app.delete("/vehicles/{v_id}")
def delete_vehicle(v_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    v = db.query(models.Vehicle).filter_by(id=v_id).first()
    if not v:
        raise HTTPException(404, "Veículo não encontrado")
    if db.query(models.RouteCityDay).filter_by(vehicle_id=v_id).first():
        raise HTTPException(400, "Remova vínculos antes.")
    db.delete(v)
    db.commit()
    return {"message": "OK"}


@app.post("/route-city-day/", response_model=schemas.RouteCityDay)
def create_link(payload: schemas.RouteCityDayBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    link = models.RouteCityDay(**payload.dict())
    db.add(link)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Erro ao vincular (possível duplicidade)")
    db.refresh(link)
    return link


@app.get("/route-city-day/", response_model=List[schemas.RouteCityDay])
def list_links(db: Session = Depends(get_db)):
    return db.query(models.RouteCityDay).all()


@app.delete("/route-city-day/{id}")
def delete_link(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    link = db.query(models.RouteCityDay).filter_by(id=id).first()
    if not link:
        raise HTTPException(404, "Vínculo não encontrado")
    db.delete(link)
    db.commit()
    return {"message": "OK"}

# ============================
# 🔎 Consultas Públicas (Geocode / Lookup)
# ============================


@app.get("/geocode/", response_model=List[schemas.GeocodeSuggestion])
async def geocode(query: str, city_name: str | None = None):
    # Dica: Adicione o user-agent para evitar bloqueio do OpenStreetMap
    q = f"{query}, {city_name}, Brasil" if city_name else f"{query}, Brasil"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": q, "format": "jsonv2", "limit": 5},
                headers={"User-Agent": "SistemaRotas/1.0"}
            )
            return [schemas.GeocodeSuggestion(
                display_name=i.get("display_name", ""),
                latitude=float(i["lat"]),
                longitude=float(i["lon"])
            ) for i in resp.json()]
        except:
            return []


@app.get("/lookup-city/")
def lookup_city(query: str, db: Session = Depends(get_db)):
    # 1. Tenta achar como Bairro
    nb = db.query(models.Neighborhood).filter(
        models.Neighborhood.name.ilike(f"%{query}%")).first()
    if nb:
        routes = db.query(models.RouteCityDay).filter_by(
            neighborhood_id=nb.id).all()
        return {
            "city": nb.city.name,
            "city_type": "Bairro",
            "routes": [{
                "route_name": r.route.name,
                "neighborhood_name": nb.name,
                "weekday": r.weekday,
                "vehicle_name": r.vehicle.name if r.vehicle else None,
                "vehicle_plate": r.vehicle.plate if r.vehicle else None,  # Add Placa
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
            "vehicle_plate": r.vehicle.plate if r.vehicle else None,  # Add Placa
            "latitude": r.neighborhood.latitude if r.neighborhood else city.latitude,
            "longitude": r.neighborhood.longitude if r.neighborhood else city.longitude
        } for r in routes]
    }

# 🔥 AQUI ESTÁ A MUDANÇA PARA O DIA 7 (TODOS OS DIAS) 🔥


@app.get("/lookup-day/", response_model=List[schemas.RouteCityDayOut])
def lookup_day(weekday: int, db: Session = Depends(get_db)):
    # Se o usuário busca "Segunda" (0), queremos trazer:
    # 1. Rotas de Segunda (0)
    # 2. Rotas de Todos os dias (7)

    # Se o usuário busca "Todos os dias" (7), trazemos só as diárias (ou tudo, depende da regra, fiz só diárias).

    target_days = [weekday, 7] if weekday != 7 else [7]

    # Usamos o operador .in_ para pegar qualquer um dos dois
    results = db.query(models.RouteCityDay).filter(
        models.RouteCityDay.weekday.in_(target_days)
    ).all()

    res = []
    for r in results:
        lat = r.neighborhood.latitude if r.neighborhood else r.city.latitude
        lng = r.neighborhood.longitude if r.neighborhood else r.city.longitude

        res.append(schemas.RouteCityDayOut(
            route_name=r.route.name,
            city_name=r.city.name,
            neighborhood_name=r.neighborhood.name if r.neighborhood else None,
            weekday=r.weekday,
            vehicle_name=r.vehicle.name if r.vehicle else None,
            vehicle_plate=r.vehicle.plate if r.vehicle else None,  # Add Placa
            latitude=lat,
            longitude=lng
        ))
    return res
