import json
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, SQLModel, select

from app.database import engine, get_db
from app.models import Item, ItemCreate, ItemResponse

with open("tokens.json", "r") as fp:
    tokens = json.load(fp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]

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
def get_items(*, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    with db as session:
        statement = select(Item).offset(skip).limit(limit)
        items = session.exec(statement).all()
        return items


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(*, db: Session = Depends(get_db), item_id: int):
    with db as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item


@app.delete("/items/{item_id}")
def delete_item(*, db: Session = Depends(get_db), item_id: int):
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
