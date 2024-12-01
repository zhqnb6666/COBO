# database/base.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL

Base = declarative_base()
print(DATABASE_URL)
engine = create_engine(
    DATABASE_URL,
    connect_args={'options': '-csearch_path=public'})
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
