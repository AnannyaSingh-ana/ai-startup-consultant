import json
import re
import ast
from crew import run_crew


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:50]


def extract_json(raw: str) -> dict:
    raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found")
    candidate = raw[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    try:
        return ast.literal_eval(candidate)
    except (ValueError, SyntaxError):
        pass
    fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
    return json.loads(fixed)


def g(d, *keys, default="N/A"):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d if d != "" else default


def format_list(items):
    if not items or not isinstance(items, list):
        return "- N/A"
    return "\n".join(f"- {item}" for item in items)


def format_sources(sources):
    if not sources or not isinstance(sources, list):
        return "- N/A"
    lines = []
    for s in sources:
        if isinstance(s, dict):
            lines.append(f"- [{s.get('name', 'Source')}]({s.get('url', '')})")
        else:
            lines.append(f"- {s}")
    return "\n".join(lines)


def build_report(plan: dict, idea: str, country: str, customer: str) -> str:
    mr = plan.get("market_research", {})
    comp = plan.get("competitor_analysis", {})
    fail = plan.get("historical_failures", {})
    fin = plan.get("finance", {})
    swot = plan.get("swot", {})
    mkt = plan.get("marketing", {})
    legal = plan.get("legal", {})
    score = plan.get("investment_score", {})
    advisor = plan.get("founder_advisor", {})

    all_sources = mr.get("sources", []) + comp.get("sources", []) + fail.get("sources", [])

    return f"""# Founders' Forge
## Business Evaluation Report

**Idea:** {idea}
**Target Country:** {country}
**Target Customer:** {customer}

---

## Executive Summary
{plan.get("overall_verdict", "N/A")}

---

## Market
**Summary:** {g(mr, "summary")}
**Estimated Market Size:** {g(mr, "estimated_market_size")}

**Demand Signals:**
{format_list(mr.get("demand_signals"))}

**Trends:**
{format_list(mr.get("market_trends"))}

**Confidence:** {g(mr, "confidence")} — {g(mr, "confidence_reason")}

---

## Competition
**Summary:** {g(comp, "summary")}

**Competitors:**
{format_list([f"{c.get('name','?')}: {c.get('positioning','?')}" for c in comp.get("competitors", [])] if comp.get("competitors") else None)}

**Market Gaps:**
{format_list(comp.get("market_gaps"))}

**Confidence:** {g(comp, "confidence")} — {g(comp, "confidence_reason")}

---

## Historical Failures
**Summary:** {g(fail, "summary")}
{format_list([f"{f.get('name','?')} ({f.get('market','?')}): {f.get('reason_for_failure','?')}" for f in fail.get("similar_failures", [])] if fail.get("similar_failures") else None)}

**Lessons:**
{format_list(fail.get("lessons"))}

---

## SWOT
**Strengths:** {format_list(swot.get("strengths"))}
**Weaknesses:** {format_list(swot.get("weaknesses"))}
**Opportunities:** {format_list(swot.get("opportunities"))}
**Threats:** {format_list(swot.get("threats"))}

---

## Finance
*{g(fin, "disclaimer")}*

- **Currency:** {g(fin, "currency")}
- **First-Year Expenses:** {g(fin, "first_year_expenses")}
- **Expected Pricing:** {g(fin, "expected_pricing")}
- **Revenue Assumptions:** {g(fin, "revenue_assumptions")}
- **CAC:** {g(fin, "cac")}
- **LTV:** {g(fin, "ltv")}
- **Gross Margin:** {g(fin, "gross_margin")}

**Assumptions:**
{format_list(fin.get("assumptions"))}

---

## Marketing
**Positioning:** {g(mkt, "positioning")}
**Go-To-Market Ideas:**
{format_list(mkt.get("go_to_market_ideas"))}

---

## Legal
{format_list(legal.get("considerations"))}

*{g(legal, "disclaimer")}*

---

## Investment Score
| Dimension | Score |
|---|---|
| Market Potential | {g(score, "market_potential")}/10 |
| Competition | {g(score, "competition")}/10 |
| Execution Difficulty | {g(score, "execution_difficulty")}/10 |
| Moat | {g(score, "moat")}/10 |
| **Overall** | **{g(score, "overall_score")}/100** |

{g(score, "reasoning")}

---

## Recommendation
**Launch?** {g(advisor, "launch_decision")}
**Reason:** {g(advisor, "reason")}
**Biggest Risk:** {g(advisor, "biggest_risk")}
**MVP:** {g(advisor, "mvp_suggestion")}
**First 100 Customers:** {g(advisor, "first_100_customers")}

**Next 30 Days:**
{format_list(advisor.get("next_30_days"))}

---

## Sources
{format_sources(all_sources)}
"""


if __name__ == "__main__":
    idea = input("Business Idea: ").strip()
    country = input("Target Country: ").strip() or "Not specified"
    customer = input("Target Customer: ").strip() or "general consumers"

    print("\nRunning agents... this will take a few minutes.\n")

    from crew import build_crew
    crew = build_crew()
    result = crew.kickoff(inputs={
        "business_idea": idea,
        "target_country": country,
        "target_customer": customer,
    })

    try:
        plan = extract_json(result.raw)
    except (ValueError, json.JSONDecodeError):
        plan = {"idea": idea, "raw_output": result.raw}

    slug = slugify(idea)
    json_path = f"reports/{slug}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    if "raw_output" not in plan:
        md_path = f"reports/{slug}.md"
        report = build_report(plan, idea, country, customer)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report)
        print("\n" + report)
        print(f"\n✅ Full report saved to {md_path} (raw data in {json_path})")
    else:
        print("\n⚠️  Could not parse structured output — raw text saved instead.")
        print(result.raw)