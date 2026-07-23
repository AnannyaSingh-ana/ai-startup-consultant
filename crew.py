from crewai import Crew, Process
from agents.market_research_agent import market_research_agent
from agents.competitor_analysis_agent import competitor_analysis_agent
from agents.historical_failures_agent import historical_failures_agent
from agents.finance_agent import finance_agent
from agents.swot_agent import swot_agent
from agents.marketing_agent import marketing_agent
from agents.legal_agent import legal_agent
from agents.investment_score_agent import investment_score_agent
from agents.founder_advisor_agent import founder_advisor_agent
from agents.manager_agent import manager_agent
from tasks import (
    market_research_task,
    competitor_analysis_task,
    historical_failures_task,
    finance_task,
    swot_task,
    marketing_task,
    legal_task,
    investment_score_task,
    founder_advisor_task,
    manager_compile_task,
)


def build_crew() -> Crew:
    return Crew(
        agents=[
            market_research_agent,
            competitor_analysis_agent,
            historical_failures_agent,
            finance_agent,
            swot_agent,
            marketing_agent,
            legal_agent,
            investment_score_agent,
            founder_advisor_agent,
            manager_agent,
        ],
        tasks=[
            market_research_task,
            competitor_analysis_task,
            historical_failures_task,
            finance_task,
            swot_task,
            marketing_task,
            legal_task,
            investment_score_task,
            founder_advisor_task,
            manager_compile_task,
        ],
        process=Process.sequential,
        verbose=True,
    )


def run_crew(business_idea: str):
    crew = build_crew()
    return crew.kickoff(inputs={"business_idea": business_idea})