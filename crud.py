# crud.py
from sqlalchemy.orm import Session
from models import User, Portfolio, Holding, TickerMetadata
from schemas import UserCreate, PortfolioCreate, HoldingCreate, TickerMetadataCreate
import httpx, asyncio, os

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")  # set in environment
# ---------------- User ----------------
def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        risk_appetite=user.risk_appetite,
        investment_horizon=user.investment_horizon,
        investment_goal=user.investment_goal,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

# ---------------- Portfolio ----------------
def create_portfolio(db: Session, portfolio: PortfolioCreate, user_id: int):
    db_portfolio = Portfolio(
        name=portfolio.name,
        cash=portfolio.cash,
        user_id=user_id
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

def get_portfolio(db: Session, portfolio_id: int):
    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

def get_user_portfolios(db: Session, user_id: int):
    return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

# ---------------- Holdings ----------------
def add_holding(db: Session, holding: HoldingCreate, portfolio_id: int):
    db_holding = Holding(
        ticker=holding.ticker,
        quantity=holding.quantity,
        portfolio_id=portfolio_id
    )
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding

# Optional helper to add multiple holdings
def add_multiple_holdings(db: Session, holdings_list: list[HoldingCreate], portfolio_id: int):
    results = []
    for holding in holdings_list:
        db_holding = add_holding(db, holding, portfolio_id)
        results.append(db_holding)
    return results

def get_portfolio_holdings(db: Session, portfolio_id: int):
    return db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()

# ---------------- Ticker Metadata ----------------
def upsert_ticker_metadata(db: Session, ticker_data: TickerMetadataCreate):
    db_ticker = db.query(TickerMetadata).filter(TickerMetadata.ticker == ticker_data.ticker).first()
    if db_ticker:
        db_ticker.sector = ticker_data.sector
        db_ticker.country = ticker_data.country
        db_ticker.industry = ticker_data.industry
    else:
        db_ticker = TickerMetadata(
            ticker=ticker_data.ticker,
            sector=ticker_data.sector,
            country=ticker_data.country,
            industry=ticker_data.industry
        )
        db.add(db_ticker)
    db.commit()
    db.refresh(db_ticker)
    return db_ticker

def get_ticker_metadata(db: Session, ticker: str):
    return db.query(TickerMetadata).filter(TickerMetadata.ticker == ticker).first()


async def analyze_saved_portfolio(db: Session, portfolio_id: int) -> dict:
    portfolio = get_portfolio(db, portfolio_id)
    if not portfolio:
        return None

    holdings = get_portfolio_holdings(db, portfolio_id)

    total_value = portfolio.cash
    holdings_result = []
    sector_distribution = {}
    country_exposure = {}

    # Fetch quotes & profiles asynchronously
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"https://finnhub.io/api/v1/quote?symbol={h.ticker}&token={FINNHUB_API_KEY}")
            for h in holdings
        ] + [
            client.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={h.ticker}&token={FINNHUB_API_KEY}")
            for h in holdings
        ]
        responses = await asyncio.gather(*tasks)

    num_holdings = len(holdings)
    quotes = [r.json() for r in responses[:num_holdings]]
    profiles = [r.json() for r in responses[num_holdings:]]

    for i, h in enumerate(holdings):
        quote_data, profile_data = quotes[i], profiles[i]
        if "c" not in quote_data or not profile_data:
            continue  # skip invalid tickers

        holding_info = {
            "ticker": h.ticker,
            "quantity": h.quantity,
            "price": quote_data["c"],
            "sector": profile_data.get("finnhubIndustry", "Unknown"),
            "country": profile_data.get("country", "Unknown"),
            "value": h.quantity * quote_data["c"]
        }

        holdings_result.append(holding_info)
        total_value += holding_info["value"]

        sector_distribution[holding_info["sector"]] = sector_distribution.get(holding_info["sector"], 0) + holding_info["value"]
        country_exposure[holding_info["country"]] = country_exposure.get(holding_info["country"], 0) + holding_info["value"]

    sector_distribution = {k: round((v / total_value) * 100, 2) for k, v in sector_distribution.items()}
    country_exposure = {k: round((v / total_value) * 100, 2) for k, v in country_exposure.items()}

    return {
        "portfolio_value": total_value,
        "cash_value": portfolio.cash,
        "holdings": holdings_result,
        "sector_distribution": sector_distribution,
        "country_exposure": country_exposure
    }