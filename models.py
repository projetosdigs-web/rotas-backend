from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    Float,
    Boolean,
)
from sqlalchemy.orm import relationship
from database import Base


# ============================
# 👤 Usuário (Admin / Login)
# ============================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


# ============================
# 🚚 Rotas
# ============================
class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

    # vínculos com cidades/bairros
    links = relationship(
        "RouteCityDay",
        back_populates="route",
        cascade="all, delete-orphan"
    )


# ============================
# 🏙️ Cidades
# ============================
class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    # coordenadas (para o mapa)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # relação com bairros
    neighborhoods = relationship(
        "Neighborhood",
        back_populates="city",
        cascade="all, delete-orphan"
    )

    # relação com rota+cidade+dia
    routes = relationship(
        "RouteCityDay",
        back_populates="city"
    )


# ============================
# 🧩 Bairros
# ============================
class Neighborhood(Base):
    __tablename__ = "neighborhoods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"))

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    city = relationship("City", back_populates="neighborhoods")
    routes = relationship("RouteCityDay", back_populates="neighborhood")


# ============================
# 🚛 Veículos (Caminhões)
# ============================
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)   # Ex.: Caminhão 01
    plate = Column(String, nullable=True)   # Ex.: ABC-1234
    active = Column(Integer, default=1)

    # relacionamento com vínculos de rota
    routes = relationship("RouteCityDay", back_populates="vehicle")


# ============================
# 🔗 Rota + Cidade + (Bairro) + Dia
# ============================
class RouteCityDay(Base):
    __tablename__ = "route_city_day"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    city_id = Column(Integer, ForeignKey("cities.id"))
    weekday = Column(Integer)  # 0..6

    # veículo (opcional)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)

    # opcional (só preenche quando quiser especificar o bairro)
    neighborhood_id = Column(
        Integer,
        ForeignKey("neighborhoods.id"),
        nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "route_id",
            "city_id",
            "neighborhood_id",
            "weekday",
            name="unique_route_city_neighborhood_day",
        ),
    )

    route = relationship("Route", back_populates="links")
    city = relationship("City", back_populates="routes")
    neighborhood = relationship("Neighborhood", back_populates="routes")
    vehicle = relationship("Vehicle", back_populates="routes")
