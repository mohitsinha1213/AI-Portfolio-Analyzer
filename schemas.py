from fastapi import HTTPException

from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Dict
from datetime import datetime
import os, httpx


FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")  # set in environment


# ---------- User Schemas ----------
class UserBase(BaseModel):
    name: str = Field(..., example="Mohit")
    risk_appetite: str = Field(..., example="Moderate")
    investment_horizon: str = Field(..., example="5 years")
    investment_goal: str = Field(..., example="Wealth Growth")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # tells Pydantic it can read from SQLAlchemy model


# ---------- Portfolio Schemas ----------
class PortfolioBase(BaseModel):
    name: str = Field(..., description = "Enter the name of the Portfolio", example="Retirement Portfolio")
    cash: float = Field(default=0.0, description = "Enter the liquid cash you have for this Portfolio", example=10000.0)

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioResponse(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Holding Schemas ----------
class HoldingBase(BaseModel):
    ticker: str = Field(..., example="AAPL")
    quantity: float = Field(..., example=10)

class HoldingCreate(HoldingBase):
    pass

class HoldingsList(BaseModel):
    holdings: List[HoldingCreate]

class HoldingResponse(HoldingBase):
    id: int
    portfolio_id: int

    class Config:
        from_attributes = True




# ---------- Ticker Metadata Schemas ----------
class TickerMetadataBase(BaseModel):
    ticker: str = Field(..., example="AAPL")
    sector: Optional[str] = Field(None, example="Technology")
    country: Optional[str] = Field(None, example="USA")
    industry: Optional[str] = Field(None, example="Consumer Electronics")

class TickerMetadataCreate(TickerMetadataBase):
    pass

class TickerMetadataResponse(TickerMetadataBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True

# -------------------------------
# User Profile
# -------------------------------
class UserProfile(BaseModel):
    risk_tolerance: Optional[str] = Field(
        None, description="User's risk tolerance level", example="medium"
    )
    investment_horizon: Optional[str] = Field(
        None, description="Investment time horizon", example="long-term"
    )
    goal: Optional[str] = Field(
        None, description="Investment goal", example="wealth growth"
    )
    country_preference: Optional[str] = Field(
        None, description="Preferred investment country", example="US"
    )


# -------------------------------
# Holdings Input
# -------------------------------
class Holding(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    quantity: int = Field(..., description="Number of shares held", example=10)


# -------------------------------
# Input Schema
# -------------------------------
class PortfolioRequest(BaseModel):
    cash: float = Field(..., description="Cash amount in portfolio", example=5000.0)
    profile: Optional[UserProfile] = Field(
        None, description="User profile containing preferences"
    )
    holdings: List[Holding] = Field(
        ..., description="List of stock holdings with tickers and quantities"
    )


# -------------------------------
# Holdings Output with Computed Field
# -------------------------------
class HoldingAnalysis(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    quantity: int = Field(..., description="Number of shares held", example=10)
    price: float = Field(..., description="Latest stock price", example=175.35)
    sector: str = Field(..., description="Sector of the company", example="Technology")
    country: str = Field(..., description="Country of the company", example="US")

    @computed_field
    @property
    def value(self) -> float:
        """Computed: total value = price * quantity"""
        return round((self.price * self.quantity), 2)
    
    
class PortfolioAnalysis(BaseModel):
    portfolio_value: float = Field(
        ..., description="Total value of portfolio including cash", example=25000.0
    )
    cash_value: float = Field(..., description="Cash held in portfolio", example=5000.0)
    cash_percent: float = Field(
        ..., description="Cash as percentage of total portfolio", example=20.0
    )
    profile: Optional[UserProfile] = Field(
        None, description="User profile provided in request"
    )
    holdings: List[HoldingAnalysis] = Field(
        ..., description="List of analyzed holdings with prices, sectors, and values"
    )
    sector_distribution: Dict[str, float] = Field(
        ..., description="Sector allocation as percentage of portfolio", example={"Technology": 40.0}
    )
    country_exposure: Dict[str, float] = Field(
        ..., description="Country allocation as percentage of portfolio", example={"US": 70.0}
    )




# -------------------------------
# Finnhub Helpers (Async)
# -------------------------------
async def fetch_stock_data(ticker: str):
    """Fetch stock price and profile from Finnhub asynchronously"""
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_API_KEY}"

    async with httpx.AsyncClient() as client:
        quote_resp, profile_resp = await client.get(quote_url), await client.get(profile_url)

    quote_data, profile_data = quote_resp.json(), profile_resp.json()

    if "c" not in quote_data or not profile_data:
        raise HTTPException(status_code=400, detail=f"Invalid ticker: {ticker}")

    return {
        "price": quote_data["c"],
        "sector": profile_data.get("finnhubIndustry", "Unknown"),
        "country": profile_data.get("country", "Unknown"),
    }


# -------------------------------
# API Route (Async)
# -------------------------------
'''@app.post("/analyze-portfolio", response_model=PortfolioAnalysis)
async def analyze_portfolio(request: PortfolioRequest):
    total_value = request.cash
    holdings_result = []
    sector_distribution = {}
    country_exposure = {}

    # Process holdings asynchronously (parallel fetches)
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"https://finnhub.io/api/v1/quote?symbol={h.ticker}&token={FINNHUB_API_KEY}")
            for h in request.holdings
        ] + [
            client.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={h.ticker}&token={FINNHUB_API_KEY}")
            for h in request.holdings
        ]
        responses = await asyncio.gather(*tasks)

    # First half = quotes, second half = profiles
    num_holdings = len(request.holdings)
    quotes = [r.json() for r in responses[:num_holdings]]
    profiles = [r.json() for r in responses[num_holdings:]]

    for i, h in enumerate(request.holdings):
        quote_data, profile_data = quotes[i], profiles[i]

        if "c" not in quote_data or not profile_data:
            raise HTTPException(status_code=400, detail=f"Invalid ticker: {h.ticker}")

        holding = HoldingAnalysis(
            ticker=h.ticker,
            quantity=h.quantity,
            price=quote_data["c"],
            sector=profile_data.get("finnhubIndustry", "Unknown"),
            country=profile_data.get("country", "Unknown"),
        )

        holdings_result.append(holding)
        total_value += holding.value

        # Update sector & country sums
        sector_distribution[holding.sector] = sector_distribution.get(holding.sector, 0) + holding.value
        country_exposure[holding.country] = country_exposure.get(holding.country, 0) + holding.value

    # Convert to percentages
    sector_distribution = {k: round((v / total_value) * 100, 2) for k, v in sector_distribution.items()}
    country_exposure = {k: round((v / total_value) * 100, 2) for k, v in country_exposure.items()}
    cash_percent = round((request.cash / total_value) * 100, 2) if total_value > 0 else 0

    return PortfolioAnalysis(
        portfolio_value=total_value,
        cash_value=request.cash,
        cash_percent=cash_percent,
        profile=request.profile,
        holdings=holdings_result,
        sector_distribution=sector_distribution,
        country_exposure=country_exposure,
    )  '''  
   

    