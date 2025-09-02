from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import crud, schemas
from typing import List

from fastapi import APIRouter

print("✅ users router loaded")


router = APIRouter(
    prefix="/holdings",
    tags=["Holdings"]
)

@router.post("/portfolio/{portfolio_id}", response_model=List[schemas.HoldingResponse])
def add_holdings(portfolio_id: int, holdings_list: schemas.HoldingsList, db: Session = Depends(get_db)):
    results = []
    for holding in holdings_list.holdings:
        result = crud.add_holding(db, holding, portfolio_id)
        results.append(result)
    return results

@router.get("/portfolio/{portfolio_id}", response_model=list[schemas.HoldingResponse])
def get_portfolio_holdings(portfolio_id: int, db: Session = Depends(get_db)):
    holdings = crud.get_portfolio_holdings(db, portfolio_id)
    if not holdings:
        raise HTTPException(status_code=404, detail="No holdings found for this portfolio")
    return holdings
