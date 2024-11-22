import os

import plyvel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "/app/db")
db = plyvel.DB(DB_PATH, create_if_missing=True)


class Item(BaseModel):
    key: str
    value: str


@app.post("/items/")
async def create_item(item: Item):
    try:
        db.put(item.key.encode(), item.value.encode())
        return {"message": "Item created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/items/{key}")
async def read_item(key: str):
    try:
        value = db.get(key.encode())
        if value is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"key": key, "value": value.decode()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/items/")
async def list_items():
    try:
        items = []
        for key, value in db.iterator():
            items.append({"key": key.decode(), "value": value.decode()})
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
