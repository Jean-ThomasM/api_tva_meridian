import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# On rÃ©cupÃ¨re l'URL depuis l'environnement ou on utilise celle par dÃ©faut (docker-compose)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meridian:meridian@localhost:5435/tva")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
