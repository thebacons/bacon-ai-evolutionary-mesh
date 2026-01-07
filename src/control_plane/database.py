import os
from sqlmodel import create_engine, Session, SQLModel
from models import Agent, Message, Node

# Database Configuration
DATABASE_PATH = os.environ.get("BACON_DB_PATH", "bacon.db")
sqlite_url = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(sqlite_url, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
