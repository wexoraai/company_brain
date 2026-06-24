from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create the asynchronous engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Create the session maker
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """Dependency to get db session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initializes extensions and database tables."""
    # We open a temporary connection using standard driver or base connection to execute CREATE EXTENSION
    async with engine.begin() as conn:
        # Enable pgvector and pg_trgm extensions in PostgreSQL if applicable
        if settings.DATABASE_URL.startswith("postgresql"):
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
                logger.info("Database extensions (vector, pg_trgm) enabled successfully.")
            except Exception as e:
                logger.warning(f"Failed to enable database extensions: {e}. If pgvector/pg_trgm are not pre-installed, this might cause issues.")
        else:
            logger.info("Running on SQLite; skipping PostgreSQL extension setup.")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized.")
