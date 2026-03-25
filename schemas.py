from pydantic import BaseModel
from typing import Optional, List

# ============================================================
# 🛣️  ROTAS
# ============================================================


class RouteBase(BaseModel):
    name: str
    description: Optional[str] = None


class RouteCreate(RouteBase):
    pass


class RouteOut(RouteBase):
    id: int

    class Config:
        from_attributes = True


# ============================================================
# 🏙️  CIDADES
# ============================================================

class CityBase(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CityCreate(CityBase):
    pass


class City(CityBase):
    id: int

    class Config:
        from_attributes = True


class CityOut(City):
    pass


# ============================================================
# 🧩  BAIRROS
# ============================================================

class NeighborhoodBase(BaseModel):
    name: str
    city_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class NeighborhoodCreate(NeighborhoodBase):
    pass


class Neighborhood(NeighborhoodBase):
    id: int

    class Config:
        from_attributes = True


class NeighborhoodOut(Neighborhood):
    pass


# ============================================================
# 🚛  VEÍCULOS
# ============================================================

class VehicleBase(BaseModel):
    name: str
    plate: Optional[str] = None
    active: int = 1


class VehicleCreate(VehicleBase):
    pass


class VehicleOut(VehicleBase):
    id: int

    class Config:
        from_attributes = True


# ============================================================
# 🔗  RELAÇÃO ROTA + CIDADE + (BAIRRO) + DIA + VEÍCULO
# ============================================================

class RouteCityDayBase(BaseModel):
    route_id: int
    city_id: int
    weekday: int  # 0..6
    neighborhood_id: Optional[int] = None
    vehicle_id: Optional[int] = None


class RouteCityDay(RouteCityDayBase):
    id: int

    class Config:
        from_attributes = True


# usado como response na consulta por dia (para o mapa)
class RouteCityDayOut(BaseModel):
    route_name: str
    city_name: str
    neighborhood_name: Optional[str] = None
    weekday: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ============================================================
# 📍 SUGESTÕES DE GEOCODIFICAÇÃO
# ============================================================

class GeocodeSuggestion(BaseModel):
    display_name: str
    latitude: float
    longitude: float
