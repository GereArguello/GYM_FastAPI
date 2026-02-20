from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, create_engine
from app.core.config import settings

# SQLite necesita un argumento especial
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # muestra queries en desarrollo
    connect_args=connect_args
)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]