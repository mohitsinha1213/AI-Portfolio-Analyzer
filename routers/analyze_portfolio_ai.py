from openai import OpenAI
from fastapi import APIRouter, Depends
import crud, httpx
import os, asyncio
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(
    prefix="/analyze-portfolio/ai",
    tags=["AI Portfolio Analysis"]
)



FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")  # set in environment


async def analyze_saved_portfolio(db: Session, portfolio_id: int) -> dict:
    portfolio = crud.get_portfolio(db, portfolio_id)
    if not portfolio:
        return None

    holdings = crud.get_portfolio_holdings(db, portfolio_id)

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


HF_API_KEY = "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"
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key = "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",
)

# ---------------- Helper: AI call ----------------
def call_ai(portfolio_data: dict):
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b:together",
        messages=[
            {
                "role": "user",
                "content": f''' You are an AI financial analyst. 
Your job is to analyze a stock portfolio and give clear insights, risks, and recommendations.

### Input:
- Cash available
- Holdings
- Sector Distribution
- Country Exposure
- User Profile:
    - Risk Tolerance
    - Investment Horizon
    - Goal:
    - Country Preference:
User Profile can be Optional
### Instructions:
1. Summarize the portfolio in plain English (easy for a beginner).
2. Identify risks (overexposure to sector, country, cash imbalance, etc.).
3. Suggest diversification strategies tailored to the user's profile.
4. Recommend 2-3 specific sectors to invest in and explain why.
5. Suggest 2-3 potential stocks (with reasoning) that match the user’s profile.
6. Keep the response concise but insightful.
7. Use numbers where possible (percentages, values).

### Output Format:
return the results as JSON with the following keys:
1. summary (short description of portfolio)
2. risks (list of risks)
3. (list of suggested improvements, diversification, potential stocks) with reasoning
4. suggested_allocation (table with asset, % target, reason)

Return the response strictly in JSON with the following structure:
        {{
            "portfolio_id": <int>,
            "ai_insights": {{
                "content": {{
                    "summary": <string>,
                    "risks": [<list of strings>],
                    "recommendations": [
                        {{
                            "title": <string>,
                            "reason": <string>
                        }}
                    ],
                    "suggested_allocation": [
                        {{
                            "asset": <string>,
                            "target%": <int>,
                            "reason": <string>
                        }}
                    ]
                }}
            }}
        }}
\n{portfolio_data}'''
            }
        ],
    )
    return completion.choices[0].message


@router.post("/{portfolio_id}")
async def analyze_portfolio_ai(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = crud.get_portfolio(db, portfolio_id)
    holdings = crud.get_portfolio_holdings(db, portfolio_id)
    
    portfolio_data = {
        "cash": portfolio.cash,
        "holdings": [{"ticker": h.ticker, "quantity": h.quantity} for h in holdings]
    }

    ai_insights = call_ai(portfolio_data)
    return {"portfolio_id": portfolio_id, "ai_insights": ai_insights}
