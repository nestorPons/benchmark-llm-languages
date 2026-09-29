from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import io
from typing import List, Dict

app = FastAPI()

class Record(BaseModel):
    id: int
    name: str
    category: str
    amount: float

class TransformRequest(BaseModel):
    records: List[Record]

@app.post("/transform")
async def transform(request: TransformRequest):
    records = request.records
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    total_amount = sum(record.amount for record in records)
    count = len(records)
    by_category = {}
    
    for record in records:
        category = record.category
        if category not in by_category:
            by_category[category] = 0
        by_category[category] += record.amount
    
    return JSONResponse(content={
        "count": count,
        "total_amount": total_amount,
        "by_category": by_category
    })

@app.post("/transform/csv")
async def transform_csv(file: UploadFile = File(...)):
    if file is None:
        raise HTTPException(status_code=400, detail="File is required")
    
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    
    if not all(col in df.columns for col in ['id', 'name', 'category', 'amount']):
        raise HTTPException(status_code=400, detail="CSV must contain id, name, category, amount columns")
    
    total_amount = df['amount'].sum()
    count = len(df)
    by_category = df.groupby('category')['amount'].sum().to_dict()
    
    return JSONResponse(content={
        "count": count,
        "total_amount": total_amount,
        "by_category": by_category
    })

@app.get("/health")
async def health():
    return JSONResponse(content={"status": "healthy"})