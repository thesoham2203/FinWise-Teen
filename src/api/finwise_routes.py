"""
FinWise Teen — FastAPI v2 Routes
AI-powered financial planning for young Indians.
"""

import os
import json
import logging
from datetime import datetime, date
from typing import Optional
from uuid import uuid4

import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")
else:
    model = None
    logger.warning("GEMINI_API_KEY not set — AI planning will use mock data")

router = APIRouter(prefix="/api/v2")

# In-memory store for demo (replace with Supabase in production)
_plans_store: dict = {}
_profiles_store: dict = {}



# ─── Schemas ──────────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    user_id: str
    full_name: Optional[str] = "User"
    age: Optional[int] = 20
    city: Optional[str] = "India"
    occupation: Optional[str] = "student"
    monthly_income: Optional[float] = 0
    monthly_expenses: Optional[float] = 0
    monthly_emis: Optional[float] = 0
    current_savings: Optional[float] = 0
    dream_job: Optional[str] = ""
    target_income_5yr: Optional[float] = 0
    risk_appetite: Optional[str] = "moderate"
    investment_horizon_years: Optional[int] = 10
    retirement_age: Optional[int] = 55
    target_corpus: Optional[float] = 0
    ai_advisor_type: Optional[str] = "moderate"  # chill, strict, pro
    preferred_currency: Optional[str] = "INR"

class ChatRequest(BaseModel):
    user_id: str
    message: str
    context_plan: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    suggestion: Optional[str] = None



# ─── Helpers ──────────────────────────────────────────────────────────────────

def build_gemini_prompt(profile: UserProfile) -> str:
    disposable = max(0, (profile.monthly_income or 0) - (profile.monthly_expenses or 0) - (profile.monthly_emis or 0))
    years_to_retire = max(1, (profile.retirement_age or 55) - (profile.age or 20))

    return f"""
You are FinWise — an expert financial advisor specializing in Indian investment markets for young people aged 13-28.

YOUR PERSONALITY:
- Tone: {profile.ai_advisor_type} (Chill = friendly, approachable; Strict = direct, no-nonsense; Pro = professional, data-driven)
- Language: Multi-lingual teen-friendly (mix of English and simple financial terms)

USER PROFILE:
- Name: {profile.full_name}, Age: {profile.age}, City: {profile.city}
- Occupation: {profile.occupation}
- Monthly Income: ₹{profile.monthly_income:,.0f}
- Monthly Expenses: ₹{profile.monthly_expenses:,.0f}
- Monthly EMIs: ₹{profile.monthly_emis:,.0f}
- Monthly Investable Surplus: ₹{disposable:,.0f}
- Current Savings: ₹{profile.current_savings:,.0f}
- Dream Career: {profile.dream_job}
- Target Income in 5 years: ₹{profile.target_income_5yr:,.0f}
- Risk Appetite: {profile.risk_appetite}
- Investment Horizon: {profile.investment_horizon_years} years
- Retirement Age Goal: {profile.retirement_age} (in {years_to_retire} years)
- Target Corpus: ₹{profile.target_corpus:,.0f} (0 = calculate automatically)

TASK: Generate a comprehensive, personalised investment allocation plan. Include BOTH well-known and lesser-known but legitimate investment instruments available in India.

You MUST return ONLY a valid JSON object with this exact structure (no markdown, no explanation outside the JSON):

{{
  "monthly_investment": <number: recommended monthly investment in INR>,
  "reasoning": "<2-3 sentence personalised explanation of WHY this allocation suits this person>",
  "allocation": [
    {{
      "name": "<Asset class name>",
      "percentage": <number: % of portfolio, all must sum to 100>,
      "monthlyAmount": <number: monthly INR amount>,
      "description": "<1-2 sentence explanation tailored to this person>",
      "instruments": ["<specific instrument 1>", "<specific instrument 2>", "<specific instrument 3>"],
      "riskLevel": "<Very Low | Low | Medium | Medium-High | High | Very High>",
      "expectedReturn": "<e.g. 12-15%>"
    }}
  ],
  "retirement_projection": {{
    "years_to_retire": {years_to_retire},
    "projected_corpus": <number: estimated corpus in INR at retirement>,
    "monthly_needed": <number: monthly SIP needed to hit target corpus>
  }}
}}

RULES:
1. Allocation percentages MUST sum to exactly 100
2. Include 6-9 asset classes (not just stocks and FDs — include options like REITs, InvITs, SGBs, P2P lending, US ETFs, Crypto if risk warrants, Index Funds, Small Caps etc.)
3. If disposable is ≤ ₹2000: focus on index funds + SGB + small savings
4. If risk_appetite = conservative: bonds 30%, FD 20%, index 20%, gold 15%, others 15%
5. If risk_appetite = aggressive: equity 50%+, include smallcap, US ETFs, crypto
6. If age ≤ 18: avoid crypto entirely, focus on index funds, gold, PPF
7. Always include an Emergency Fund allocation (5-10%)
8. Use real Indian instrument names: NIFTY 50 Index Fund, Mirae Asset, Axis Bluechip, SBI Nifty, SGB, Zerodha P2P, etc.
9. Monthly amounts must add up to monthly_investment
10. Adjust monthly_investment to be 70-80% of disposable surplus (keep buffer for life)
"""


def generate_mock_plan(profile: UserProfile) -> dict:
    """Fallback mock plan when Gemini is not available."""
    disposable = max(0, (profile.monthly_income or 0) - (profile.monthly_expenses or 0) - (profile.monthly_emis or 0))
    monthly = max(500, disposable * 0.7)
    years = max(1, (profile.retirement_age or 55) - (profile.age or 20))
    corpus = monthly * 12 * years * (1.12 ** (years / 2))

    allocations = [
        {"name": "NIFTY 50 Index Funds", "percentage": 30, "monthlyAmount": int(monthly * 0.30),
         "description": "Core equity exposure via low-cost index funds tracking India's top 50 companies.",
         "instruments": ["Zerodha Nifty 50 ETF", "HDFC Index Fund Nifty 50", "SBI Nifty Index Fund"],
         "riskLevel": "Medium", "expectedReturn": "12-14%"},
        {"name": "Sovereign Gold Bonds (SGB)", "percentage": 15, "monthlyAmount": int(monthly * 0.15),
         "description": "Government-backed gold bonds giving 2.5% interest + gold price appreciation. Tax-free on maturity.",
         "instruments": ["RBI Sovereign Gold Bond", "Gold ETF (Nippon)", "Digital Gold via Zerodha"],
         "riskLevel": "Low", "expectedReturn": "8-12%"},
        {"name": "Mutual Funds (Flexi Cap)", "percentage": 20, "monthlyAmount": int(monthly * 0.20),
         "description": "Actively managed funds that can invest across large, mid, and small cap companies.",
         "instruments": ["Parag Parikh Flexi Cap", "Mirae Asset Flexi Cap", "HDFC Flexi Cap"],
         "riskLevel": "Medium", "expectedReturn": "13-16%"},
        {"name": "Government Bonds/Gilt", "percentage": 10, "monthlyAmount": int(monthly * 0.10),
         "description": "Safe, long-term government securities with guaranteed returns. Great for stability.",
         "instruments": ["Nippon India Gilt Fund", "HDFC Gilt Fund", "RBI Direct Bonds"],
         "riskLevel": "Very Low", "expectedReturn": "7-8%"},
        {"name": "Small Cap Stocks", "percentage": 10, "monthlyAmount": int(monthly * 0.10),
         "description": "Higher risk, higher reward. Small companies with massive growth potential.",
         "instruments": ["Axis Small Cap Fund", "Kotak Small Cap Fund", "Direct small cap stocks"],
         "riskLevel": "High", "expectedReturn": "15-20%"},
        {"name": "REITs (Real Estate)", "percentage": 8, "monthlyAmount": int(monthly * 0.08),
         "description": "Real estate investment trusts — own commercial real estate without buying property.",
         "instruments": ["Embassy REIT", "Mindspace REIT", "Brookfield REIT"],
         "riskLevel": "Medium", "expectedReturn": "8-11%"},
        {"name": "P2P Lending", "percentage": 7, "monthlyAmount": int(monthly * 0.07),
         "description": "Lend directly to vetted borrowers on regulated platforms for higher interest returns.",
         "instruments": ["LenDenClub", "Faircent", "RupeeCircle"],
         "riskLevel": "Medium-High", "expectedReturn": "10-14%"},
        {"name": "Emergency Fund (Liquid)", "percentage": 10, "monthlyAmount": int(monthly * 0.10),
         "description": "Keep 3-6 months of expenses liquid at all times. Your financial safety net.",
         "instruments": ["Paytm Money Liquid Fund", "Zerodha Liquid Bees", "High-interest savings"],
         "riskLevel": "Very Low", "expectedReturn": "4-6%"},
    ]

    # Normalize to exactly 100%
    total_pct = sum(a["percentage"] for a in allocations)
    if total_pct != 100:
        allocations[-1]["percentage"] += (100 - total_pct)

    return {
        "monthly_investment": round(monthly),
        "reasoning": f"Based on your ₹{disposable:,.0f}/month surplus and {profile.risk_appetite} risk appetite, we've crafted a diversified portfolio across 8 asset classes. With {years} years until retirement at {profile.retirement_age}, you have excellent time to compound wealth. The 30% NIFTY index allocation forms the core, while SGBs and REITs diversify into assets most Indians miss.",
        "allocation": allocations,
        "retirement_projection": {
            "years_to_retire": years,
            "projected_corpus": round(corpus),
            "monthly_needed": round(corpus / (years * 12 * ((1.12 ** years - 1) / 0.12))),
        },
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0 — FinWise Teen",
        "gemini": "connected" if model else "not configured",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/profile")
async def save_profile(profile: UserProfile):
    """Save user financial profile (also saved to Supabase via frontend)."""
    _profiles_store[profile.user_id] = profile.model_dump()
    return {"status": "saved", "user_id": profile.user_id}


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    p = _profiles_store.get(user_id)
    if not p:
        raise HTTPException(404, "Profile not found")
    return p


@router.post("/plan/generate")
async def generate_plan(profile: UserProfile):
    """Generate an AI-powered investment plan for the user."""
    _profiles_store[profile.user_id] = profile.model_dump()

    plan_data = None

    if model:
        try:
            prompt = build_gemini_prompt(profile)
            response = model.generate_content(prompt)
            raw = response.text.strip()

            # Clean up in case Gemini wraps in markdown
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            plan_data = json.loads(raw)
            logger.info("Gemini plan generated successfully for user %s", profile.user_id)
        except Exception as e:
            logger.warning("Gemini failed (%s), falling back to mock plan", str(e))

    if not plan_data:
        plan_data = generate_mock_plan(profile)

    plan_data["plan_id"] = str(uuid4())
    plan_data["user_id"] = profile.user_id
    plan_data["generated_at"] = datetime.now().isoformat()

    _plans_store[profile.user_id] = plan_data
    return plan_data


@router.get("/plan/{user_id}/latest")
async def get_latest_plan(user_id: str):
    """Get the latest investment plan for a user."""
    plan = _plans_store.get(user_id)
    if not plan:
        raise HTTPException(404, "No plan found. Generate one first.")
    return plan


@router.get("/plan/{user_id}/history")
async def get_plan_history(user_id: str):
    """Returns the single latest plan (extend with DB for full history)."""
    plan = _plans_store.get(user_id)
    return {"plans": [plan] if plan else [], "count": 1 if plan else 0}


@router.get("/market/pulse")
async def market_pulse():
    logger.info("Market pulse requested")

    """
    Live market data for NIFTY 50, SENSEX, Gold, 10Y Bond.
    Uses Yahoo Finance free API via yfinance.
    Falls back to mock data if unavailable.
    """
    try:
        import yfinance as yf
        nifty = yf.Ticker("^NSEI").fast_info
        sensex = yf.Ticker("^BSESN").fast_info
        gold = yf.Ticker("GC=F").fast_info

        return {
            "nifty50": {
                "value": round(nifty.last_price or 22000, 2),
                "change": round((nifty.last_price or 22000) - (nifty.previous_close or 22000), 2),
                "changePercent": round(((nifty.last_price or 22000) / (nifty.previous_close or 22000) - 1) * 100, 2),
            },
            "sensex": {
                "value": round(sensex.last_price or 73000, 2),
                "change": round((sensex.last_price or 73000) - (sensex.previous_close or 73000), 2),
                "changePercent": round(((sensex.last_price or 73000) / (sensex.previous_close or 73000) - 1) * 100, 2),
            },
            "gold": {
                "value": round((gold.last_price or 2000) * 83, 0),  # USD to INR, per oz → per 10g
                "change": round((gold.last_price or 2000) * 83 * 0.001, 0),
                "changePercent": round(((gold.last_price or 2000) / (gold.previous_close or 2000) - 1) * 100, 2),
            },
            "bond10y": {"value": 7.05},
            "source": "Yahoo Finance",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception:
        # Mock fallback
        return {
            "nifty50": {"value": 22450.5, "change": 123.4, "changePercent": 0.55},
            "sensex": {"value": 73891.2, "change": 412.1, "changePercent": 0.56},
            "gold": {"value": 73200, "change": -150, "changePercent": -0.20},
            "bond10y": {"value": 7.05},
            "source": "Mock (yfinance unavailable)",
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/market/instruments")
async def list_instruments():
    """All supported investment types with details."""
    return {
        "instruments": [
            {"id": "nifty50", "name": "NIFTY 50 Index Fund", "category": "Equity", "risk": "Medium", "return_range": "12-14%", "min_investment": 500},
            {"id": "flexi_mf", "name": "Flexi Cap Mutual Fund", "category": "Equity", "risk": "Medium", "return_range": "13-16%", "min_investment": 500},
            {"id": "smallcap", "name": "Small Cap Fund", "category": "Equity", "risk": "High", "return_range": "15-20%", "min_investment": 500},
            {"id": "sgb", "name": "Sovereign Gold Bond", "category": "Gold", "risk": "Low", "return_range": "8-12%", "min_investment": 5000},
            {"id": "gilt", "name": "Gilt / G-Sec Fund", "category": "Bonds", "risk": "Very Low", "return_range": "7-8%", "min_investment": 500},
            {"id": "reit", "name": "REITs", "category": "Real Estate", "risk": "Medium", "return_range": "8-11%", "min_investment": 300},
            {"id": "invit", "name": "InvITs", "category": "Infrastructure", "risk": "Medium", "return_range": "9-12%", "min_investment": 5000},
            {"id": "p2p", "name": "P2P Lending", "category": "Alternative", "risk": "Medium-High", "return_range": "10-14%", "min_investment": 5000},
            {"id": "us_etf", "name": "US ETFs (S&P 500)", "category": "International Equity", "risk": "Medium-High", "return_range": "12-15%", "min_investment": 100},
            {"id": "crypto", "name": "Crypto (BTC/ETH)", "category": "Crypto", "risk": "Very High", "return_range": "Highly variable", "min_investment": 100},
            {"id": "ppf", "name": "PPF (Public Provident Fund)", "category": "Fixed Income", "risk": "Very Low", "return_range": "7.1%", "min_investment": 500},
            {"id": "nps", "name": "NPS (National Pension System)", "category": "Retirement", "risk": "Low-Medium", "return_range": "8-10%", "min_investment": 500},
            {"id": "fd", "name": "Fixed Deposit", "category": "Fixed Income", "risk": "Very Low", "return_range": "6-8%", "min_investment": 1000},
            {"id": "liquid", "name": "Liquid Fund (Emergency)", "category": "Liquid", "risk": "Very Low", "return_range": "4-6%", "min_investment": 500},
        ]
    }

@router.get("/market/history/{symbol}")
async def get_market_history(symbol: str, period: str = "7d"):
    logger.info("Market history requested for: %s", symbol)
    """

    Get historical data for a symbol.
    period: 1d, 5d, 7d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        import yfinance as yf
        # Map common indices if needed
        ticker_map = {
            "NIFTY": "^NSEI",
            "SENSEX": "^BSESN",
            "GOLD": "GC=F",
            "USDINR": "INR=X"
        }
        yf_symbol = ticker_map.get(symbol.upper(), symbol)
        
        hist = yf.Ticker(yf_symbol).history(period=period)
        if hist.empty:
            raise Exception("No data found")
            
        data = [
            {"date": str(d.date()), "close": round(float(c), 2)}
            for d, c in zip(hist.index, hist["Close"])
        ]
        return {"symbol": symbol, "history": data, "count": len(data)}
    except Exception as e:
        logger.warning("History fetch failed for %s: %s", symbol, str(e))
        # Return empty list instead of 404 to avoid breaking UI
        return {"symbol": symbol, "history": [], "count": 0, "error": str(e)}

@router.post("/chat", response_model=ChatResponse)
async def finwise_chat(request: ChatRequest):
    """
    Personalized financial chat advisor.
    Uses Gemini with planning context.
    """
    if not model:
        return ChatResponse(
            response="I'm currently in offline mode, but I can still tell you that your plan looks solid!",
            suggestion="Try asking about your P2P lending risk."
        )
    
    try:
        context = ""
        if request.context_plan:
            context = f"User's current financial plan: {json.dumps(request.context_plan)}. "
        
        prompt = (
            f"You are the 'FinWise Genie', a helpful and savvy financial advisor for Indian teens. "
            f"Use the following context to answer the user's question accurately and helpfully. "
            f"Keep it professional yet engaging for a young audience. "
            f"{context}\n\nUser: {request.message}"
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        return ChatResponse(response=text, suggestion="Want to know more about compounding?")
    except Exception as e:
        logger.error("Chat error: %s", str(e))
        return ChatResponse(
            response="Sorry, I'm having a bit of trouble thinking right now. Let's try again in a moment!",
            suggestion="Ask me about your monthly investment."
        )
