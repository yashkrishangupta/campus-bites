from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database
DATABASE_URL = "sqlite:///./campusbites.db"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()


# Database connection dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables and add newer columns to an existing database (no data is lost)
def ensure_schema():
    from backend import models  # noqa: F401  (registers the tables)

    Base.metadata.create_all(bind=engine)

    review_columns = {c["name"] for c in inspect(engine).get_columns("reviews")}

    if "is_demo" not in review_columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE reviews ADD COLUMN is_demo BOOLEAN DEFAULT 0")
            )
