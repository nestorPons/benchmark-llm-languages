import base64
import hashlib
import hmac
import json
import sqlite3
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI()
DB = "test.db"
SECRET = b"benchmark-secret"
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = conn()
    c.executescript(open("data/schema.sql").read())
    h = hashlib.sha256(b"secret").hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", h))
    c.commit()
    c.close()


def make_token(username):
    payload = json.dumps({"sub": username, "exp": time.time() + 3600})
    b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    sig = hmac.new(SECRET, b64.encode(), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"


def verify_token(token):
    try:
        b64, sig = token.split(".")
        pad = "=" * (-len(b64) % 4)
        if hmac.compare_digest(hmac.new(SECRET, b64.encode(), hashlib.sha256).hexdigest(), sig):
            payload = json.loads(base64.urlsafe_b64decode(b64 + pad))
            if payload["exp"] > time.time():
                return payload
    except Exception:
        pass
    return None


def current_user(token: str = Depends(oauth2)):
    p = verify_token(token)
    if not p:
        raise HTTPException(401, "Invalid token")
    return p


class Login(BaseModel):
    username: str
    password: str


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float


# --- duplicated price validation (T8 exercise: extract to a module) ---
def _check_price_create(price: float):
    if price < 0:
        raise HTTPException(400, "price must be >= 0")


def _check_price_update(price: float):
    if price < 0:
        raise HTTPException(400, "price must be >= 0")
# --- end duplicated block ---


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/auth/login")
def login(body: Login):
    c = conn()
    row = c.execute("SELECT * FROM users WHERE username=?", (body.username,)).fetchone()
    c.close()
    h = hashlib.sha256(body.password.encode()).hexdigest()
    if not row or row["password"] != h:
        raise HTTPException(401, "Incorrect username or password")
    return {"token": make_token(body.username)}


@app.post("/items", status_code=201)
def create(item: Item, user=Depends(current_user)):
    _check_price_create(item.price)
    c = conn()
    cur = c.execute("INSERT INTO items (name, description, price) VALUES (?,?,?)",
                    (item.name, item.description, item.price))
    c.commit()
    row = c.execute("SELECT * FROM items WHERE id=?", (cur.lastrowid,)).fetchone()
    c.close()
    return dict(row)


@app.get("/items")
def list_items(user=Depends(current_user)):
    c = conn()
    rows = c.execute("SELECT * FROM items").fetchall()
    c.close()
    return [dict(r) for r in rows]


@app.get("/items/{item_id}")
def get_item(item_id: int, user=Depends(current_user)):
    c = conn()
    row = c.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    c.close()
    if not row:
        raise HTTPException(404, "not found")
    return dict(row)


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, user=Depends(current_user)):
    _check_price_update(item.price)
    c = conn()
    cur = c.execute("UPDATE items SET name=?, description=?, price=? WHERE id=?",
                    (item.name, item.description, item.price, item_id))
    c.commit()
    c.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "not found")
    return {"id": item_id, **item.model_dump()}


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, user=Depends(current_user)):
    c = conn()
    cur = c.execute("DELETE FROM items WHERE id=?", (item_id,))
    c.commit()
    c.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "not found")


init()
