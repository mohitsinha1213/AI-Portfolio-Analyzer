from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import crud, schemas

from fastapi import APIRouter

print("✅ users router loaded")

router = APIRouter(
    prefix="/portfolios",
    tags=["Portfolios"]
)

@router.post("/user/{user_id}", response_model=schemas.PortfolioResponse)
def create_portfolio(user_id: int, portfolio: schemas.PortfolioCreate, db: Session = Depends(get_db)):
    return crud.create_portfolio(db, portfolio, user_id)

@router.get("/{portfolio_id}", response_model=schemas.PortfolioResponse)
def read_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    db_portfolio = crud.get_portfolio(db, portfolio_id)
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return db_portfolio

@router.get("/user/{user_id}", response_model=list[schemas.PortfolioResponse])
def list_user_portfolios(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_portfolios(db, user_id)
