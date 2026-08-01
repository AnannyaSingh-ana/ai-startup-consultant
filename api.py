"""
Founders' Forge API
--------------------
FastAPI wrapper around the existing CrewAI pipeline (crew.py -> build_crew()).

Endpoint:
    POST /generate-plan
        body: { "business_idea": str, "target_country": str, "target_customer": str }
        returns: { "success": bool, "plan": dict | None, "raw_output": str | None, "error": str | None }
"""

import json
import re
import logging

from fastapi import FastAPI, HTTPException, Depends
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from crew import build_crew  # this must match the function name in your existing crew.py
from database import Base, engine, get_db
from datetime import date
from models import BusinessPlan, DailyUsage
from config import GENERATION_ENABLED, DAILY_REPORT_LIMIT

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("founders-forge-api")

# ---------------------------------------------------------------------------
# FastAPI app setup
# ---------------------------------------------------------------------------
app = FastAPI(title="Founders' Forge API")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Rate limit exceeded. Please try again later."
        },
    )

# Creates the business_plans table if it doesn't exist yet, every time the
# app starts. Fine for early development. Once your schema stabilizes,
# you'd normally switch to a migration tool (Alembic) instead — flag it
# when you're ready and we'll set that up.
Base.metadata.create_all(bind=engine)

# CORS: lets your Next.js frontend (running on a different port/domain) call this API.
# "*" is fine for local dev. Before deploying, replace with your real frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class GeneratePlanRequest(BaseModel):
    business_idea: str
    target_country: str
    target_customer: str


class GeneratePlanResponse(BaseModel):
    success: bool
    plan: dict | None = None
    raw_output: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Helper: pull clean JSON out of the crew's raw text output
# ---------------------------------------------------------------------------
def extract_json(raw_text: str) -> dict:
    """
    CrewAI's raw output is sometimes:
      - pure JSON
      - JSON wrapped in ```json ... ``` fences
      - JSON with extra commentary text around it
    This tries each strategy in order until one parses successfully.
    """
    text = raw_text.strip()

    # Strategy 1: try parsing directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip ```json ... ``` or ``` ... ``` fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: grab from the first { to the last } in the text
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from crew output")


# ---------------------------------------------------------------------------
# Helper: turn strings like "750,000", "₹5,000", "40%" into plain numbers
# ---------------------------------------------------------------------------
def parse_number(value) -> float | None:
    """
    Strips currency symbols, commas, percent signs, and whitespace from a
    string and returns a float. Returns None if nothing numeric is found.
    Already-numeric values are returned as-is (as float).
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value)
    # Keep only digits, minus sign, and decimal point
    cleaned = re.sub(r"[^\d\.\-]", "", text)
    if cleaned in ("", "-", "."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def recompute_breakeven(finance: dict) -> dict:
    """
    Recalculates breakeven_months in Python instead of trusting the LLM's
    arithmetic. Formula:
        monthly_revenue = expected_pricing * assumed_customers_month_12
        monthly_surplus = monthly_revenue - monthly_burn
        breakeven_months = startup_cost / monthly_surplus

    Mutates and returns the same finance dict. If any required field is
    missing or unparseable, or the business never breaks even (surplus <= 0),
    leaves a clear note instead of a made-up number.
    """
    startup_cost = parse_number(finance.get("startup_cost"))
    monthly_burn = parse_number(finance.get("monthly_burn"))
    price = parse_number(finance.get("expected_pricing"))
    customers = parse_number(finance.get("assumed_customers_month_12"))

    if None in (startup_cost, monthly_burn, price, customers):
        finance["theoretical_breakeven_months"] = "Unavailable"
        
        return finance

    monthly_revenue = price * customers
    monthly_surplus = monthly_revenue - monthly_burn
    finance["monthly_revenue"] = round(monthly_revenue, 2)
    finance["monthly_surplus"] = round(monthly_surplus, 2)

    if monthly_surplus <= 0:
        finance["breakeven_months"] = "Not reached at this scale"
        finance["breakeven_note"] = (
            f"At {customers:.0f} customers, monthly revenue "
            f"({monthly_revenue:,.0f}) does not exceed monthly burn "
            f"({monthly_burn:,.0f}), so this business does not break even "
            "at this assumed customer count. Needs more customers, higher "
            "pricing, or lower burn."
        )
        return finance

    breakeven_months = startup_cost / monthly_surplus
    finance["theoretical_breakeven_months"] = round(breakeven_months, 1)
    finance["startup_cost"] = round(startup_cost, 2)
    finance["monthly_burn"] = round(monthly_burn, 2)
    finance["expected_pricing"] = round(price, 2)
    finance["assumed_customers_month_12"] = round(customers)
    finance["breakeven_note"] = (
        f"Recalculated in code: {startup_cost:,.0f} startup cost / "
        f"({monthly_revenue:,.0f} monthly revenue - {monthly_burn:,.0f} "
        f"monthly burn = {monthly_surplus:,.0f} surplus) = "
        f"{breakeven_months:.1f} months."
    )
    return finance


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def health_check():
    """Simple route to confirm the server is up. Visit http://127.0.0.1:8000/ in a browser."""
    return {"status": "ok", "message": "Founders' Forge API is running"}


@app.post("/generate-plan", response_model=GeneratePlanResponse)
@limiter.limit("2/hour")

def generate_plan(
    request: Request,
    request_data: GeneratePlanRequest,
    db: Session = Depends(get_db),
):
    logger.info(f"Received request for idea: {request_data.business_idea!r}")
    if not GENERATION_ENABLED:
     raise HTTPException(
        status_code=503,
        detail="Report generation is temporarily disabled while the demo is undergoing maintenance.",
    )

    # ------------------------------------------------------------------
    # Global daily usage limit
    # ------------------------------------------------------------------
    today = date.today()

    usage = (
        db.query(DailyUsage)
        .filter(DailyUsage.day == today)
        .first()
    )

    if usage is None:
        usage = DailyUsage(
            day=today,
            reports_generated=0
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)

    if usage.reports_generated >= DAILY_REPORT_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Today's demo limit has been reached. Please try again tomorrow."
        )

    # ------------------------------------------------------------------
    # Run CrewAI
    # ------------------------------------------------------------------
    try:
        crew = build_crew()

        result = crew.kickoff(
        inputs={
            "business_idea": request_data.business_idea,
            "target_country": request_data.target_country,
            "target_customer": request_data.target_customer,
        }
    )

    except Exception as e:
        logger.exception("Crew execution failed")

        error_message = str(e)

        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            raise HTTPException(
                status_code=429,
                detail=(
                    "The AI service is currently busy. Please wait a moment and try again."
                
            ),
        )

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the business plan.",
    )

    raw_output = result.raw if hasattr(result, "raw") else str(result)

    # ------------------------------------------------------------------
    # Parse JSON
    # ------------------------------------------------------------------
    try:
        plan = extract_json(raw_output)

    except ValueError as e:
        logger.error(f"JSON parsing failed: {e}")

        return GeneratePlanResponse(
            success=False,
            raw_output=raw_output,
            error=(
                "Agents ran successfully but the output could not be parsed as JSON. "
                "Raw output is included below so you can inspect it."
            ),
        )

    # ------------------------------------------------------------------
    # Recalculate breakeven
    # ------------------------------------------------------------------
    if isinstance(plan, dict) and isinstance(plan.get("finance"), dict):
        plan["finance"] = recompute_breakeven(plan["finance"])

    # ------------------------------------------------------------------
    # Save plan
    # ------------------------------------------------------------------
    try:
        db_plan = BusinessPlan(
            business_idea=request_data.business_idea,
            target_country=request_data.target_country,
            target_customer=request_data.target_customer,
            plan_json=plan,
        )

        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)

        logger.info(f"Saved plan to database with id={db_plan.id}")

    except Exception:
        logger.exception("Failed to save plan to database")
        db.rollback()

    # ------------------------------------------------------------------
    # Count ONLY successful generations
    # ------------------------------------------------------------------
    usage.reports_generated += 1
    db.commit()

    return GeneratePlanResponse(
        success=True,
        plan=plan,
    )
    


@app.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    """Returns a summary (no full plan_json) of every saved plan, most recent first."""
    plans = db.query(BusinessPlan).order_by(BusinessPlan.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "business_idea": p.business_idea,
            "target_country": p.target_country,
            "target_customer": p.target_customer,
            "created_at": p.created_at,
        }
        for p in plans
    ]


@app.get("/plans/{plan_id}")
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Returns one saved plan in full, including plan_json."""
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail=f"No plan found with id={plan_id}")
    return {
        "id": plan.id,
        "business_idea": plan.business_idea,
        "target_country": plan.target_country,
        "target_customer": plan.target_customer,
        "created_at": plan.created_at,
        "plan": plan.plan_json,
    }