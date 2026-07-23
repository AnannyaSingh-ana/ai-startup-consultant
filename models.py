from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from database import Base


class BusinessPlan(Base):
    __tablename__ = "business_plans"

    id = Column(Integer, primary_key=True, index=True)
    business_idea = Column(String, nullable=False)
    target_country = Column(String, nullable=False)
    target_customer = Column(String, nullable=False)

    # The full structured plan (market research, finance, SWOT, etc.)
    # stored as native Postgres JSONB so it's queryable later if needed.
    plan_json = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())