from pathlib import Path
from typing import List

import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data.json"
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"


class Item(BaseModel):
    id: int
    text: str


class ItemCreate(BaseModel):
    text: str


app = FastAPI(title="Simple FastAPI List")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def read_items() -> List[Item]:
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []
    return [Item(**item) for item in data]


def write_items(items: List[Item]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump([item.dict() for item in items], f, ensure_ascii=False, indent=2)


@app.get("/", response_class=HTMLResponse)
def root():
    """
    Главная страница сразу отдаёт наш фронтенд.
    """
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=500, detail="index.html не найден")
    return INDEX_FILE.read_text(encoding="utf-8")


@app.get("/items", response_model=List[Item])
def list_items():
    return read_items()


@app.post("/items", response_model=Item, status_code=201)
def add_item(item: ItemCreate):
    items = read_items()
    next_id = max((i.id for i in items), default=0) + 1
    new_item = Item(id=next_id, text=item.text)
    items.append(new_item)
    write_items(items)
    return new_item


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    items = read_items()
    new_items = [i for i in items if i.id != item_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    write_items(new_items)
    return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
