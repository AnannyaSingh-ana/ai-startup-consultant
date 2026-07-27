from crewai import Task
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

GEO_GUARDRAIL = (
    "IMPORTANT: The target country is '{target_country}'. If this says 'Not "
    "specified' or is otherwise unclear, do NOT assume any country, city, or "
    "region (e.g. do not default to the USA, California, or any specific "
    "city). In that case, either give country-agnostic advice that would "
    "apply broadly, or explicitly state that country-specific advice "
    "requires knowing the target country. Never invent a country, city, "
    "regulator, or law that wasn't given or found via search."
)

market_research_task = Task(
    description=(
        "Research whether there is real demand for '{business_idea}' "
        "specifically in {target_country}, targeting {target_customer}. "
        "If a country is specified, include it explicitly in your search "
        "queries. Find: "
        "(1) evidence of customer demand or pain points, "
        "(2) relevant market trends or news from the last 1-2 years, "
        "(3) any market size or growth data specific to that market. "
        "Only report what you actually find — do not fabricate statistics "
        "or substitute data from a different country. Note the source name "
        "and URL for every fact. Judge your own confidence: High if multiple "
        "independent sources agree, Medium if thin, Low if you had to infer "
        "heavily. " + GEO_GUARDRAIL
    ),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{"demand_signals": [...], "market_trends": [...], '
        '"estimated_market_size": "...", "summary": "...", '
        '"sources": [{"name": "...", "url": "..."}], '
        '"confidence": "High/Medium/Low", "confidence_reason": "..."}. '
        "Each list should contain 3-5 short strings. Include 3-6 sources."
    ),
    agent=market_research_agent,
)

competitor_analysis_task = Task(
    description=(
        "Search for real businesses similar to '{business_idea}' operating "
        "in {target_country}, serving {target_customer}. Identify local "
        "competitors and locally relevant distribution platforms if a "
        "country is specified. Do not default to competitors or platforms "
        "from a different country. Note the source name and URL for each. "
        "Judge your confidence accordingly. " + GEO_GUARDRAIL
    ),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{"competitors": [{"name": "...", "positioning": "..."}], '
        '"market_gaps": [...], "summary": "...", '
        '"sources": [{"name": "...", "url": "..."}], '
        '"confidence": "High/Medium/Low", "confidence_reason": "..."}. '
        "List 2-5 competitors if found. Include 2-5 sources."
    ),
    agent=competitor_analysis_agent,
)

historical_failures_task = Task(
    description=(
    "Search for real businesses similar to '{business_idea}' that failed. "
    "You MUST run at least one search that explicitly includes the words "
    "'{target_country}' before considering any other country. Only use "
    "examples from outside {target_country} if that search genuinely "
    "returns nothing relevant, and in that case, actively look across "
    "MULTIPLE different countries rather than defaulting to the United "
    "States — do not include more than one US-based example unless no "
    "other country's example exists at all. Note the source name and URL "
    "for each case. " + GEO_GUARDRAIL
),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{"similar_failures": [{"name": "...", "reason_for_failure": "...", '
        '"market": "..."}], "lessons": [...], "summary": "...", '
        '"sources": [{"name": "...", "url": "..."}], '
        '"confidence": "High/Medium/Low", "confidence_reason": "..."}. '
        'The "market" field must state which country that failure example '
        "is actually from."
    ),
    agent=historical_failures_agent,
)

finance_task = Task(
    description=(
    "Build an illustrative financial model for '{business_idea}' "
    "targeting {target_customer}, based on the market and competitor "
    "research provided as context. If {target_country} is known, use "
    "its local currency; if not, use generic units (e.g. 'local "
    "currency units') rather than defaulting to USD. "

    "First, decide realistic assumptions for: "
    "(1) price per customer, "
    "(2) expected paying customers by month 12, "
    "(3) startup costs, and "
    "(4) monthly operating costs. "

    "From these assumptions, estimate: "
    "startup_cost (one-time launch costs), "
    "monthly_burn (average ongoing monthly operating costs), "
    "expected_pricing, "
    "assumed_customers_month_12, "
    "CAC, "
    "LTV, "
    "gross_margin, and "
    "realistic_breakeven_months. "

    "IMPORTANT: realistic_breakeven_months is NOT a mathematical calculation. "
    "It should estimate when a real startup would likely reach break-even "
    "after accounting for gradual customer acquisition, slow early growth, "
    "marketing ramp-up, onboarding delays, and other real-world factors. "
    "Do not simply divide startup_cost by monthly profit. The backend will "
    "calculate the theoretical break-even separately. "

    "Scale every cost to the actual nature of this business. "
    "A solo founder, home-based business, SaaS MVP, or digital product "
    "should have much lower startup costs than a full commercial operation. "
    "Only include expensive equipment, inventory, office rent, or hiring "
    "when the business genuinely requires them. "

    "The assumptions section must clearly explain every number you chose, "
    "including pricing, customer count, startup cost breakdown, monthly "
    "burn breakdown, CAC reasoning, LTV reasoning, gross margin reasoning, "
    "and why the realistic break-even timeline is longer than the "
    "theoretical financial calculation if applicable. "

    "Every number must be clearly labeled as an illustrative planning "
    "assumption, not a researched or verified figure. "
    + GEO_GUARDRAIL
),
    expected_output=(
    "A JSON object with EXACTLY these fields: "
    '{"currency": "...", '
    '"startup_cost": "...", '
    '"monthly_burn": "...", '
    '"realistic_breakeven_months": "...", '
    '"expected_pricing": "...", '
    '"assumed_customers_month_12": "...", '
    '"cac": "...", '
    '"ltv": "...", '
    '"gross_margin": "...", '
    '"assumptions": [...], '
    '"disclaimer": "These figures are illustrative planning '
    'assumptions only, not researched or verified estimates."}. '

    'The "assumptions" list must clearly explain: '
    '(1) expected pricing, '
    '(2) expected paying customers by month 12, '
    '(3) startup cost breakdown, '
    '(4) monthly burn breakdown, '
    '(5) CAC reasoning, '
    '(6) LTV reasoning, '
    '(7) gross margin reasoning, '
    '(8) the arithmetic used to calculate theoretical monthly revenue '
    '(expected_pricing × assumed_customers_month_12), and '
    '(9) why the realistic_breakeven_months is longer than the theoretical '
    'financial break-even whenever applicable. '
    'Do not calculate theoretical break-even yourself; the backend will '
    'calculate it automatically.'
),
agent=finance_agent,
context=[market_research_task, competitor_analysis_task],
)

swot_task = Task(
    description=(
        "Using the market research, competitor analysis, and historical "
        "failure findings provided as context, produce a SWOT analysis for "
        "'{business_idea}'. Base it only on the research provided — do not "
        "introduce new geographic assumptions. " + GEO_GUARDRAIL
    ),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{"strengths": [...], "weaknesses": [...], "opportunities": [...], '
        '"threats": [...]}. Each list should have 2-4 short items.'
    ),
    agent=swot_agent,
    context=[market_research_task, competitor_analysis_task, historical_failures_task],
)

marketing_task = Task(
    description=(
        "Using the market research and competitor analysis provided as "
        "context, develop a realistic early-stage marketing strategy for "
        "'{business_idea}' targeting {target_customer}. "

        "If {target_country} is known, recommend only locally relevant "
        "marketing channels and platforms supported by the research. "
        "Do not invent cities, platforms, influencers, or communities. "
        "If the country is unknown, keep recommendations generic "
        "(e.g. local marketplaces, local social platforms, industry events). "

        "Prioritize low-cost, founder-friendly customer acquisition rather "
        "than enterprise-scale marketing. Focus on what a startup could "
        "actually execute during its first few months with limited resources. "

        "For every acquisition channel, briefly explain WHY it fits this "
        "business and target customer. Rank channels from highest to lowest "
        "expected ROI. Suggest measurable KPIs rather than vague marketing "
        "advice. "
        + GEO_GUARDRAIL
    ),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{'
        '"positioning": "...", '
        '"ideal_customer_message": "...", '
        '"launch_strategy": "...", '
        '"customer_acquisition_channels": ['
        '{"channel":"...", "reason":"...", "priority":1},'
        '{"channel":"...", "reason":"...", "priority":2}'
        '], '
        '"kpis":[...], '
        '"biggest_marketing_risk":"...", '
        '"go_to_market_ideas":[...]'
        '}. '
        'Include 3–5 customer acquisition channels ranked by priority and '
        '3–5 concrete go-to-market ideas.'
    ),
    agent=marketing_agent,
    context=[
        market_research_task,
        competitor_analysis_task,
    ],
)
legal_task = Task(
    description=(
        "Flag realistic legal, licensing, and compliance considerations for "
        "'{business_idea}'. If {target_country} is known, tailor to that "
        "country's regulatory bodies (only ones you're confident actually "
        "apply). If country is unknown, give generic categories of "
        "consideration (e.g. 'food safety licensing', 'business registration', "
        "'sales tax/VAT registration') without naming a specific country's "
        "agencies. Always include a 'not legal advice' disclaimer. "
        + GEO_GUARDRAIL
    ),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{"considerations": [...], "disclaimer": "This is not legal advice. '
        'Consult a licensed local attorney for guidance specific to your '
        'business and country."}.'
    ),
    agent=legal_agent,
)

investment_score_task = Task(
    description=(
        "Using the market research, competitor analysis, historical "
        "failures, and finance model provided as context, evaluate "
        "'{business_idea}' like an experienced early-stage investor. "
        "Score each category honestly based ONLY on the research provided. "
        "Do not inflate scores to encourage the founder. "

        "Score the following dimensions (each out of 10): "
        "(1) Market Potential, "
        "(2) Competition (10 = weak competition, 1 = extremely competitive), "
        "(3) Execution Difficulty (10 = relatively easy to execute, "
        "1 = extremely difficult), "
        "(4) Moat. "

        "IMPORTANT: Do NOT assign the Moat score directly. "
        "First evaluate these five components, each scored from 0–2: "
        "(a) Brand Advantage, "
        "(b) Technology/IP Advantage, "
        "(c) Network Effects, "
        "(d) Switching Costs, "
        "(e) Proprietary Data or Distribution Advantage. "

        "The Moat score must equal the sum of those five component scores "
        "(maximum 10). Briefly justify every component score. "

        "Finally compute an overall score out of 100 as a balanced synthesis "
        "of all findings. The overall score should reflect investability, "
        "not just market size. Businesses with great markets but brutal "
        "competition or weak differentiation should not receive very high "
        "overall scores."
    ),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{'
        '"market_potential": X, '
        '"competition": X, '
        '"execution_difficulty": X, '
        '"moat": X, '
        '"moat_breakdown": {'
        '"brand_advantage": {"score": X, "reason": "..."}, '
        '"technology_ip": {"score": X, "reason": "..."}, '
        '"network_effects": {"score": X, "reason": "..."}, '
        '"switching_costs": {"score": X, "reason": "..."}, '
        '"data_distribution": {"score": X, "reason": "..."}'
        '}, '
        '"overall_score": X, '
        '"reasoning": "..."'
        '}. '
        'The moat score MUST equal the sum of the five moat component scores.'
    ),
    agent=investment_score_agent,
    context=[
        market_research_task,
        competitor_analysis_task,
        historical_failures_task,
        finance_task,
    ],
)

founder_advisor_task = Task(
    description=(
    "Using ALL research provided as context for '{business_idea}', give "
    "the founder a direct recommendation. Be honest even if the answer "
    "is 'no' or 'not yet'. Write the launch_decision and reason like a "
    "sharp, no-fluff startup mentor talking straight to the founder — "
    "direct, punchy, opinionated, 1-2 sentences max for each. Cut hedging "
    "language and filler phrases; say the real thing plainly. STRICT RULE: "
    "only recommend actions, locations, products, or strategies that are "
    "directly supported by the prior agents' outputs. Do not invent cities, "
    "regions, product variations, or tactics that weren't mentioned in the "
    "research context. If the research doesn't give you enough to answer a "
    "field confidently (e.g. no clear MVP angle emerged from the research), "
    "explicitly say so — for example: 'The research doesn't specify a "
    "particular city/product angle, so no specific recommendation is "
    "made here.' Never fill gaps with plausible-sounding invention."
    "If different agent outputs conflict with each other, explain which evidence"
    "you trust more and base your recommendation on that rather than averaging"
    "or ignoring the conflict. "
    + GEO_GUARDRAIL
),
    expected_output=(
        "A JSON object with exactly these fields: "
        '{"launch_decision": "YES/NO/NOT YET", "reason": "...", '
        '"biggest_risk": "...", "mvp_suggestion": "...", '
        '"first_100_customers": "...", "next_30_days": [...]}. '
        "Every field must be traceable to something in the provided context "
        "— if not enough evidence exists for a field, say so explicitly "
        "instead of inventing specifics."
    ),
    agent=founder_advisor_agent,
    context=[
        market_research_task,
        competitor_analysis_task,
        historical_failures_task,
        finance_task,
        swot_task,
        legal_task,
        investment_score_task,
    ],
)

manager_compile_task = Task(
    description=(
        "Using ALL the research provided as context, compile one complete "
        "business plan for '{business_idea}' targeting {target_customer} "
        "(target country: {target_country}). Do not invent new facts, "
        "locations, or regulations beyond what your team already found. "
        "Carry forward every 'sources', 'confidence', 'confidence_reason' "
        "field, the finance disclaimer, the investment score, and the "
        "founder advisor recommendation exactly as given."
    ),
    expected_output=(
        "A single JSON object with exactly these top-level fields: "
        '{"idea": "...", "target_country": "...", "target_customer": "...", '
        '"market_research": {...}, "competitor_analysis": {...}, '
        '"historical_failures": {...}, "finance": {...}, "swot": {...}, '
        '"marketing": {...}, "legal": {...}, "investment_score": {...}, '
        '"founder_advisor": {...}, "overall_verdict": "..."}.'
    ),
    agent=manager_agent,
    context=[
        market_research_task,
        competitor_analysis_task,
        historical_failures_task,
        finance_task,
        swot_task,
        marketing_task,
        legal_task,
        investment_score_task,
        founder_advisor_task,
    ],
)