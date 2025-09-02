from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base   


# ---------------- User Table ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    risk_appetite = Column(String, nullable=False)           
    investment_horizon = Column(String, nullable=False)      
    investment_goal = Column(String, nullable=False)         
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    portfolios = relationship("Portfolio", back_populates="user")


# ---------------- Portfolio Table ----------------
class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)    
    cash = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio")


# ---------------- Holdings Table ----------------
class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    ticker = Column(String, nullable=False)  
    quantity = Column(Float, nullable=False)

    portfolio = relationship("Portfolio", back_populates="holdings")


# ---------------- Ticker Metadata Table ----------------
class TickerMetadata(Base):
    __tablename__ = "ticker_metadata"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, nullable=False, index=True)
    sector = Column(String, nullable=True)
    country = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PortfolioAIInsights(Base):
    __tablename__ = "portfolio_ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    insights = Column(String)
