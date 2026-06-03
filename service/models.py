
from sqlalchemy import Column, Integer, String, Numeric, Float, ForeignKey, SmallInteger, DateTime
from sqlalchemy.orm import relationship
from database import Base
"""
Esquema para la Base de Datos usando SQLArchemy (Para ORM)
Se traducen las  tablas PostgreSQL a clases de Python para trabajar con ellas como objetos
"""
class Usuario(Base):
    __tablename__ = "users"

    userid = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    userrole = Column(String(50), nullable=False)
    balance = Column(Numeric(10, 2), nullable=False, default=0.00)
    nationality = Column(String(100), nullable=False, default='España') 
    cart_total = Column(Numeric(10, 2), nullable=False, default=0.00)          
    discount = Column(Numeric(5, 2), nullable=False, default=0.00)

class Movie(Base):
    __tablename__ = "movies"

    movieid = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    moviedescription = Column(String(255))
    movieyear = Column(Integer)
    genre = Column(String(100))
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)              
    average_rating = Column(Numeric(3, 2), default=0.00)

class Actor(Base):
    __tablename__ = "actors"

    actorid = Column(Integer, primary_key=True)
    actorname = Column(String(255), nullable=False)

class MovieActor(Base):
    __tablename__ = "movie_actors"

    movieid = Column(Integer, ForeignKey("movies.movieid"), primary_key=True)
    actorid = Column(Integer, ForeignKey("actors.actorid"), primary_key=True)

class CartItem(Base):
    __tablename__ = "cart_items"

    userid = Column(Integer, ForeignKey("users.userid"), primary_key=True)
    movieid = Column(Integer, ForeignKey("movies.movieid"), primary_key=True)

class Order(Base):
    __tablename__ = "orders"

    orderid = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey("users.userid"), nullable=False)
    order_date = Column(String, nullable=False) 
    total_price = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True))  
class OrderItem(Base):
    __tablename__ = "order_items"

    orderid = Column(Integer, ForeignKey("orders.orderid"), primary_key=True)
    movieid = Column(Integer, ForeignKey("movies.movieid"), primary_key=True)
    price_at_purchase = Column(Numeric(5, 2), nullable=False)

class MovieVote(Base):
    __tablename__ = "movie_votes"

    userid = Column(Integer, ForeignKey("users.userid"), primary_key=True)
    movieid = Column(Integer, ForeignKey("movies.movieid"), primary_key=True)
    rating = Column(SmallInteger, nullable=False)
