from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import settings


engine = create_async_engine(settings.async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from models import user, job, application, notification  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Ajout des colonnes manquantes (compatibilité SQLite et PostgreSQL)
        new_columns = [
            ("users", "gender", "VARCHAR"),
            ("users", "school", "VARCHAR"),
            ("users", "education_level", "VARCHAR"),
        ]
        for table, column, col_type in new_columns:
            try:
                if settings.is_postgres:
                    await conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                    ))
                else:
                    await conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                    ))
            except Exception:
                pass  # Colonne déjà présente
