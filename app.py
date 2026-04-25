"""
Agentic AI Security Intelligence — Flask API
=============================================
Input: company domain
Output: projects, teams, tech stack, people signals, context
"""

import json
import sys
from pathlib import Path
from functools import lru_cache
from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy import create_engine, text

# Add the files directory to path so we can import the extractor
sys.path.insert(0, str(Path(__file__).parent / "files"))
from extractor import JDExtractor
from curated_domains import CURATED_DOMAINS

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", static_url_path="/static")

CH_ENGINE = create_engine(
    "clickhouse+http://reo_readonly_user:fghjkvbnwe4567DFGH@10.10.0.43:8123/default"
)

MAX_JDS_PER_DOMAIN = 50

# Initialize the extractor once (loads all 3 YAML dictionaries)
EXT = JDExtractor(
    keywords_path=Path(__file__).parent / "files" / "keywords.yaml",
    projects_master_path=Path(__file__).parent / "files" / "projects_master.yaml",
    context_signals_path=Path(__file__).parent / "files" / "context_signals.yaml",
)

# Load taxonomy from projects_master.yaml for the UI
import yaml
with open(Path(__file__).parent / "files" / "projects_master.yaml") as f:
    _PROJECTS_MASTER = yaml.safe_load(f)


# ---------------------------------------------------------------------------
# ClickHouse queries
# ---------------------------------------------------------------------------

def fetch_jds_for_domain(domain: str) -> list[dict]:
    """Fetch JDs from ClickHouse for a given company domain."""
    query = text("""
        SELECT
            job_title,
            job_description,
            job_department,
            job_level,
            job_seniority,
            company_name,
            job_posted_date,
            job_location_city,
            job_location_country_code,
            is_remote,
            tech_function,
            is_active
        FROM org_jobs
        WHERE company_domain = :domain
          AND job_description != ''
          AND length(job_description) > 100
        ORDER BY job_posted_date DESC
        LIMIT :limit
    """)
    with CH_ENGINE.connect() as conn:
        rows = conn.execute(query, {"domain": domain, "limit": MAX_JDS_PER_DOMAIN}).fetchall()

    results = []
    for r in rows:
        results.append({
            "title": r[0] or "",
            "description": r[1] or "",
            "department": r[2] or "",
            "level": r[3] or "",
            "seniority": r[4] or "",
            "company_name": r[5] or "",
            "posted_date": str(r[6]) if r[6] else "",
            "city": r[7] or "",
            "country": r[8] or "",
            "is_remote": bool(r[9]) if r[9] else False,
            "tech_function": r[10] or "",
            "is_active": bool(r[11]) if r[11] else False,
        })
    return results


def fetch_tech_function_breakdown(domain: str) -> list[dict]:
    """Get team/function breakdown by counting tech_function values."""
    query = text("""
        SELECT
            tech_function,
            count() as cnt
        FROM org_jobs
        WHERE company_domain = :domain
          AND tech_function != ''
        GROUP BY tech_function
        ORDER BY cnt DESC
        LIMIT 30
    """)
    with CH_ENGINE.connect() as conn:
        rows = conn.execute(query, {"domain": domain}).fetchall()
    return [{"function": r[0], "count": r[1]} for r in rows]


def fetch_domain_summary(domain: str) -> dict:
    """Get quick stats for a domain."""
    query = text("""
        SELECT
            any(company_name) as company_name,
            count() as total_jobs,
            countIf(is_active = 1) as active_jobs,
            min(job_posted_date) as earliest_post,
            max(job_posted_date) as latest_post
        FROM org_jobs
        WHERE company_domain = :domain
    """)
    with CH_ENGINE.connect() as conn:
        r = conn.execute(query, {"domain": domain}).fetchone()
    return {
        "company_name": r[0] or domain,
        "total_jobs": r[1],
        "active_jobs": r[2],
        "earliest_post": str(r[3]) if r[3] else None,
        "latest_post": str(r[4]) if r[4] else None,
    }


# ---------------------------------------------------------------------------
# Analysis engine
# ---------------------------------------------------------------------------

def analyze_domain(domain: str) -> dict:
    """Full analysis: fetch JDs → run extractor → build company profile."""
    domain = domain.strip().lower()

    # Fetch from ClickHouse
    jds_raw = fetch_jds_for_domain(domain)
    if not jds_raw:
        return {"error": f"No job descriptions found for domain: {domain}", "domain": domain}

    summary = fetch_domain_summary(domain)
    tech_functions = fetch_tech_function_breakdown(domain)
    company_name = summary.get("company_name", domain)

    # Build JD list for the extractor
    jds_for_extractor = []
    jd_details = []  # keep raw details for per-JD view
    for jd in jds_raw:
        jds_for_extractor.append({
            "text": jd["description"],
            "title": jd["title"],
            "team_hint": jd["department"],
        })
        # Run per-JD extraction too
        r = EXT.extract(
            jd_text=jd["description"],
            title=jd["title"],
            team_hint=jd["department"],
            company=company_name,
        )
        jd_detail = {
            "title": jd["title"],
            "department": jd["department"],
            "level": jd["level"],
            "seniority": jd["seniority"],
            "posted_date": jd["posted_date"],
            "city": jd["city"],
            "country": jd["country"],
            "is_remote": jd["is_remote"],
            "tech_function": jd["tech_function"],
            "is_active": jd["is_active"],
            "extracted_teams": [t["canonical"] for t in r.team[:3]],
            "extracted_projects": [
                {
                    "canonical": p["canonical"],
                    "score": p["score"],
                    "confidence": p["confidence"],
                    "maturity": p["maturity"],
                    "parent_category": p["parent_category"],
                }
                for p in r.project_v2[:5]
            ],
            "extracted_tech": r.tech,
            "extracted_people": r.people,
        }
        jd_details.append(jd_detail)

    # Aggregate company profile
    profile = EXT.profile_company(company_name, jds_for_extractor)

    # Serialize sets to lists
    for p in profile.get("projects", []):
        if isinstance(p.get("personas_hired"), set):
            p["personas_hired"] = sorted(p["personas_hired"])

    # Build compound signals
    confirmed_projects = {p["key"] for p in profile.get("projects", [])
                          if p.get("score", 0) >= 4}
    compounds = _detect_compounds(confirmed_projects)

    return {
        "domain": domain,
        "company_name": company_name,
        "summary": summary,
        "tech_function_breakdown": tech_functions,
        "profile": profile,
        "compound_signals": compounds,
        "jd_details": jd_details,
        "jds_analyzed": len(jds_raw),
    }


def _detect_compounds(confirmed_keys: set) -> list[dict]:
    """Detect compound signals from confirmed project keys."""
    compounds = _PROJECTS_MASTER.get("compound_signals", {})
    results = []
    for name, spec in compounds.items():
        for combo in spec.get("requires_any_of", []):
            if all(k in confirmed_keys for k in combo):
                results.append({
                    "key": name,
                    "description": spec.get("description", ""),
                    "implication": spec.get("implication", ""),
                    "triggered_by": combo,
                })
                break
    return results


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/analyze/<domain>")
def api_analyze(domain):
    try:
        result = analyze_domain(domain)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/domains")
def api_domains():
    return jsonify(CURATED_DOMAINS)


@app.route("/api/taxonomy")
def api_taxonomy():
    """Return the project taxonomy for the UI."""
    categories = _PROJECTS_MASTER.get("categories", {})
    out = {}
    for cat_key, cat in categories.items():
        out[cat_key] = {
            "description": cat.get("description", ""),
            "color": cat.get("color", "#666"),
            "subprojects": {}
        }
        for sp_key, sp in cat.get("subprojects", {}).items():
            out[cat_key]["subprojects"][sp_key] = {
                "canonical": sp["canonical"],
                "strong_phrases": sp.get("strong_phrases", [])[:3],
                "medium_phrases": sp.get("medium_phrases", [])[:3],
            }
    return jsonify(out)


@app.route("/api/search-domain")
def api_search_domain():
    """Search for domains matching a query string."""
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return jsonify([])

    query = text("""
        SELECT
            company_domain,
            any(company_name) as company_name,
            count() as job_count
        FROM org_jobs
        WHERE company_domain LIKE :pattern
          AND company_domain != ''
        GROUP BY company_domain
        ORDER BY job_count DESC
        LIMIT 15
    """)
    with CH_ENGINE.connect() as conn:
        rows = conn.execute(query, {"pattern": f"%{q}%"}).fetchall()

    return jsonify([
        {"domain": r[0], "name": r[1] or r[0], "job_count": r[2]}
        for r in rows
    ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Agentic AI Security Intelligence Platform")
    print("  http://localhost:5001")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5001, debug=True)
