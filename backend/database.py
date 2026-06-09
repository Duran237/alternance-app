import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger(__name__)


engine = create_async_engine(settings.async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def _purge_school_jobs(conn) -> None:
    """Supprime de la DB les offres d'établissements scolaires déjà enregistrées."""
    try:
        from services.scraper import _is_educational_institution, _is_training_role
        result = await conn.execute(text("SELECT id, company, title FROM jobs"))
        rows = result.fetchall()
        ids_to_delete = [
            r[0] for r in rows
            if _is_educational_institution(r[1] or "", r[2] or "") or _is_training_role(r[2] or "")
        ]
        if ids_to_delete:
            await conn.execute(text(f"DELETE FROM jobs WHERE id IN ({','.join(str(i) for i in ids_to_delete)})"))
            logger.info(f"[DB] Purge (écoles + rôles formation) : {len(ids_to_delete)} offres supprimées")
    except Exception as e:
        logger.debug(f"[DB] Purge ignorée : {e}")


async def init_db():
    from models import user, job, application, notification  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Supprimer les offres d'établissements scolaires déjà en base
        await _purge_school_jobs(conn)
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
