from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

from routers import users, portfolios, holdings, ticker_metadata, analyze_portfolio_ai



app = FastAPI(
    title="Portfolio Analyzer API",
    description="Analyze stock portfolio using Finnhub data",
    version="1.0.0"
)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")  # set in environment



# Register CRUD routers
app.include_router(users.router)
app.include_router(portfolios.router)
app.include_router(holdings.router)
app.include_router(ticker_metadata.router)

app.include_router(analyze_portfolio_ai.router)




print("Routers are being imported...")
print("Users router:", users)
print("Portfolios router:", portfolios)
print("Holdings router:", holdings)
print("Ticker Metadata router:", ticker_metadata)
print("AI Analysis router:", analyze_portfolio_ai)
