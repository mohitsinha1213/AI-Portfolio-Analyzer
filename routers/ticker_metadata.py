from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import crud, schemas

from fastapi import APIRouter

print("✅ users router loaded")

router = APIRouter(
    prefix="/ticker-metadata",
    tags=["Ticker Metadata"]
)

@router.post("/", response_model=schemas.TickerMetadataResponse)
def upsert_ticker_metadata(ticker: schemas.TickerMetadataCreate, db: Session = Depends(get_db)):
    return crud.upsert_ticker_metadata(db, ticker)

@router.get("/{ticker}", response_model=schemas.TickerMetadataResponse)
def get_ticker_metadata(ticker: str, db: Session = Depends(get_db)):
    db_ticker = crud.get_ticker_metadata(db, ticker)
    if not db_ticker:
        raise HTTPException(status_code=404, detail="Ticker metadata not found")
    return db_ticker
