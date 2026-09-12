import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("EMAIL_DB_URL")
if not DATABASE_URL:
    database_path = os.getenv("EMAIL_DB_PATH", "data/emails.db")
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{database_path}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
