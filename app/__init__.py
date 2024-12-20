import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, SQLModel, select

from app.database import engine, get_db
from app.models import Item, ItemCreate, ItemResponse

load_dotenv()
APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent
tokens_path = ROOT_DIR / "tokens.json"
with open(tokens_path, "r") as fp:
    tokens = json.load(fp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

origins = os.getenv("CORS_ORIGINS", "").split(",")

AUTHORIZED_TOKENS = tokens
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in AUTHORIZED_TOKENS.values():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized token",
        )
    return token


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/items/", response_model=ItemResponse)
def create_item(
    *,
    db: Session = Depends(get_db),
    item: ItemCreate,
    token: str = Depends(verify_token)
):
    with db as session:
        db_item = Item.model_validate(item)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item


@app.get("/items/", response_model=List[ItemResponse])
def get_items(*, db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    with db as session:
        statement = select(Item).offset(skip).limit(limit)
        items = session.exec(statement).all()
        return items


@app.get("/items/latest/{key}/", response_model=ItemResponse)
def get_latest(*, key: str, db: Session = Depends(get_db)):
    with db as session:
        statement = (
            select(Item)
            .where(Item.key == key)
            .order_by(Item.created_at.desc())  # type: ignore[attr-defined]
        )
        items = session.exec(statement).first()
        return items


@app.get("/items/type/{key}", response_model=List[ItemResponse])
def get_items_by_key(*, db: Session = Depends(get_db), limit: int = 10, key: str):
    with db as session:
        statement = (
            select(Item)
            .where(Item.key == key)
            .order_by(Item.id.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        items = session.exec(statement).all()
        items.reverse()
        return items


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(*, db: Session = Depends(get_db), item_id: int):
    with db as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item


@app.delete("/items/{item_id}")
def delete_item(
    *, db: Session = Depends(get_db), item_id: int, token: str = Depends(verify_token)
):
    with db as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Sensor not found")

        session.delete(item)
        session.commit()
        return {"ok": True}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {"status": "error", "message": str(exc), "type": type(exc).__name__}
