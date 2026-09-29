from fastapi import HTTPException

def check_price_create(price: float):
    if price < 0:
        raise HTTPException(400, "price must be >= 0")

def check_price_update(price: float):
    if price < 0:
        raise HTTPException(400, "price must be >= 0")