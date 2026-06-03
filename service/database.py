from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
"""
Se establece la conexión entre la Base de Datos y mi codigo Python
"""
DATABASE_URL = "postgresql+asyncpg://alumnodb:1234@db:5432/si1"

engine = create_async_engine(DATABASE_URL, echo=True)

Base = declarative_base()

async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)