"""
Flask API for the Hybrid Tech Project Classifier UI.
Runs on port 5002.
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import text, create_engine
from project_categories import classify_company, CATEGORY_BY_ID
import os, time, json, ast, re
from datetime import datetime
from collections import Counter

app = Flask(__name__, static_folder='static/classifier', static_url_path='')
CORS(app)

_CH_USER = os.getenv('CH_USER', 'reo_readonly_user')
_CH_PASS = os.getenv('CH_PASS', 'fghjkvbnwe4567DFGH')
_CH_HOST = os.getenv('CH_HOST', '20.185.50.64')       # public endpoint (Render-accessible)
_CH_LI_HOST = os.getenv('CH_LI_HOST', '20.185.50.64') # LinkedIn DB — same public host

CH_ENGINE = create_engine(f'clickhouse+http://{_CH_USER}:{_CH_PASS}@{_CH_HOST}:8123/default')
CH_LI     = create_engine(f'clickhouse+http://{_CH_USER}:{_CH_PASS}@{_CH_LI_HOST}:8123/default')

@app.route('/')
def index():
    return send_from_directory('static/classifier', 'index.html')

@app.route('/api/classify', methods=['POST'])
def classify():
    """
    POST body: { "domains": ["wiz.io", "sysdig.com", ...], "use_claude": true }
    """
    data = request.json
    domains = [d.strip().lower() for d in data.get('domains', []) if d.strip()]
    use_claude = data.get('use_claude', False)

    if not domains:
        return jsonify({"error": "No domains provided"}), 400

    # Fetch jobs from ClickHouse
    domain_sql = ", ".join([f"'{d}'" for d in domains])
    query = f"""
        SELECT company_domain, job_title, job_description, job_url, all_skills_slugs, job_posted_date
        FROM org_jobs_inter
        WHERE job_status = 'active' AND company_domain IN ({domain_sql})
    """

    start = time.time()
    try:
        with CH_ENGINE.connect() as conn:
            rows = conn.execute(text(query)).fetchall()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}", "results": {}, "meta": {}}), 500
        
    # Contextual Personas per Project ID
    PROJECT_PERSONAS = {
        "A1": r"(?i)cloud|infrastructure|devops",
        "A2": r"(?i)release|devops|platform",
        "A3": r"(?i)finops|engineering|cloud op",
        "A4": r"(?i)devsecops|security|platform",
        "A5": r"(?i)cloud solution|enterprise architect|it director|infrastructure",
        "B1": r"(?i)site reliability|sre|systems|devops",
        "B2": r"(?i)incident|sre|engineering",
        "B3": r"(?i)platform|developer experience|devex|infrastructure",
        "B4": r"(?i)software|backend|fullstack|application",
        "C1": r"(?i)data|analytics",
        "C2": r"(?i)distributed|streaming|data|kafka|event",
        "C3": r"(?i)ai|machine learning|software",
        "C4": r"(?i)mlops|machine learning",
        "C5": r"(?i)data governance|data steward|data",
        "C6": r"(?i)bi\b|analytics|product",
        "D1": r"(?i)application security|appsec|devsecops|security",
        "D2": r"(?i)cloud security|secops|security architect|ciso",
        "D3": r"(?i)iam|identity|security",
        "D4": r"(?i)soc|security operations|threat|security",
        "D5": r"(?i)network security|security|it director",
        "E1": r"(?i)sdet|qa|quality|test|automation",
        "E2": r"(?i)api|backend|developer advocate|engineering",
        "E3": r"(?i)frontend|web|design system|ui|ux",
        "E4": r"(?i)ios|android|mobile",
        "E5": r"(?i)devex|developer productivity|engineering|software",
        "F1": r"(?i)integration|enterprise architect|systems analyst|engineering",
        "F2": r"(?i)database|dba|backend|data"
    }

    # Fetch people from LinkedIn DB
    domain_people = {}
    try:
        with CH_LI.connect() as conn:
            p_query = f"""
                SELECT company_domain, full_name, position_title, linkedin_url, seniority 
                FROM profile_positions_enriched 
                WHERE company_domain IN ({domain_sql}) 
                  AND is_current = 1 
                  AND tech_flag = 1 
                  AND seniority IN ('Director', 'VP', 'CXO', 'Head', 'Partner', 'Manager', 'Senior', 'Lead', 'Principal')
                LIMIT 1000
            """
            p_rows = conn.execute(text(p_query)).fetchall()
            seen_names = set()
            for pr in p_rows:
                dom = pr[0]
                name = pr[1]
                if name in seen_names:
                    continue
                seen_names.add(name)
                
                if dom not in domain_people:
                    domain_people[dom] = []
                domain_people[dom].append({
                    "name": name,
                    "role": pr[2],
                    "url": pr[3],
                    "seniority": pr[4]
                })
    except Exception as e:
        print("Error fetching LinkedIn people:", e)
        
    fetch_time = time.time() - start

    # Group jobs by domain
    domain_jobs = {}
    for r in rows:
        dom = r[0]
        if dom not in domain_jobs:
            domain_jobs[dom] = []
        # r: domain, title, desc, url, skills, date
        domain_jobs[dom].append((r[1], r[2], r[3], r[4], r[5]))

    # Classify per domain
    results = {}
    total_regex = 0
    total_claude = 0
    unmatched_global = []

    for dom in domains:
        jobs = domain_jobs.get(dom, [])
        if not jobs:
            results[dom] = {"total_jobs": 0, "projects": [], "unmatched_count": 0}
            continue

        job_entries = []
        parsed_jobs = []
        
        for idx, (title, desc, job_url, all_skills_str, job_posted_date) in enumerate(jobs):
            # clickhouse-sqlalchemy returns Array columns as Python lists directly
            if isinstance(all_skills_str, list):
                parsed_skills = all_skills_str
            elif isinstance(all_skills_str, str) and all_skills_str:
                try:
                    parsed_skills = ast.literal_eval(all_skills_str)
                except:
                    parsed_skills = []
            else:
                parsed_skills = []
                    
            days_ago = 999
            if job_posted_date:
                try:
                    date_obj = job_posted_date if isinstance(job_posted_date, datetime) else datetime.fromisoformat(str(job_posted_date))
                    days_ago = (datetime.now() - date_obj).days
                except:
                    pass
                    
            job_entries.append({
                "title": title,
                "slugs": parsed_skills,
                "days_ago": days_ago
            })
            parsed_jobs.append({
                "title": title,
                "desc": desc,
                "url": job_url,
                "skills": parsed_skills,
                "date": job_posted_date,
                "days_ago": days_ago
            })

        # Run the v2 engine
        classification = classify_company(dom, job_entries)
        
        all_projects = []
        exclude = {'software-development', 'agile-methodology', 'problem-solving', 'troubleshooting', 'communication-skills'}
        
        for cat_info in classification.get("qualifying", []):
            cat_id = cat_info["id"]
            cat_obj = CATEGORY_BY_ID[cat_id]
            
            project_data = {
                "name": cat_info["name"],
                "project": cat_info["name"],  # Add both to ensure UI compatibility
                "domain": cat_info["domain"],
                "job_count": cat_info["matching_jobs"],
                "evidence": [],
                "skills": [],
                "source": "v2_engine",
                "latest_job_date": None,
                "people": []
            }
            
            # Match contextual personas
            all_folks = domain_people.get(dom, [])
            persona_regex = PROJECT_PERSONAS.get(cat_id, r"(?i)engineer|architect|manager")
            
            matched_people = []
            fallback_people = []
            
            for f in all_folks:
                if re.search(persona_regex, f["role"]):
                    matched_people.append(f)
                elif f["seniority"] in ['Director', 'VP', 'CXO', 'Head']:
                    fallback_people.append(f)
            
            # Prioritize Economic Buyers over ICs among matched
            buyers = [p for p in matched_people if p["seniority"] in ['Director', 'VP', 'CXO', 'Head', 'Partner']]
            champions = [p for p in matched_people if p["seniority"] not in ['Director', 'VP', 'CXO', 'Head', 'Partner']]
            
            final_people = buyers + champions
            if not final_people:
                final_people = fallback_people
                
            project_data["people"] = final_people[:5]
            
            # Extract evidence
            for j in parsed_jobs:
                slugs_set = set(j["skills"])
                title_match = any(re.search(p, j["title"], re.IGNORECASE) for p in cat_obj.job_title_patterns)
                matched_slugs = list(slugs_set & set(cat_obj.all_slugs()))
                has_slug = bool(matched_slugs)
                
                if title_match or has_slug:
                    project_data["skills"].extend(j["skills"])
                    if j["date"]:
                        if not project_data["latest_job_date"] or j["date"] > project_data["latest_job_date"]:
                            project_data["latest_job_date"] = j["date"]
                            
                    if len(project_data["evidence"]) < 10:
                        excerpt = j["desc"][:200] + "..." if j["desc"] else ""
                        keyword_str = ", ".join(matched_slugs[:5]) if matched_slugs else "Title match"
                        project_data["evidence"].append({
                            "job_title": j["title"],
                            "job_url": j["url"],
                            "keyword": keyword_str,
                            "excerpt": excerpt
                        })

            # Calculate top technologies
            valid_skills = [s for s in project_data["skills"] if s not in exclude]
            project_data["top_technologies"] = [x[0] for x in Counter(valid_skills).most_common(20)]
            
            # Format date
            if project_data["latest_job_date"]:
                if isinstance(project_data["latest_job_date"], datetime):
                    project_data["latest_job_date"] = project_data["latest_job_date"].isoformat()
                else:
                    project_data["latest_job_date"] = str(project_data["latest_job_date"])

            all_projects.append(project_data)

        total_regex += len(jobs)

        results[dom] = {
            "total_jobs": len(jobs),
            "projects": all_projects,
            "people": domain_people.get(dom, []),
            "unmatched_count": 0,
            "regex_classified": len(jobs),
        }

    classify_time = time.time() - start - fetch_time

    return jsonify({
        "results": results,
        "meta": {
            "domains_requested": len(domains),
            "domains_with_jobs": len([d for d in results if results[d]["total_jobs"] > 0]),
            "total_jobs_fetched": len(rows),
            "fetch_time_sec": round(fetch_time, 2),
            "classify_time_sec": round(classify_time, 2),
            "total_regex_matched": total_regex,
            "total_claude_classified": total_claude,
        }
    })

@app.route('/api/health')
def health():
    try:
        with CH_ENGINE.connect() as conn:
            count = conn.execute(text("SELECT count() FROM org_jobs_inter WHERE job_status='active' LIMIT 1")).fetchone()[0]
        return jsonify({"status": "ok", "active_jobs": count})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route('/api/taxonomy')
def taxonomy():
    from project_categories import CATEGORIES
    return jsonify({
        "categories": [c.name for c in CATEGORIES],
        "keyword_counts": {c.name: len(c.all_slugs()) for c in CATEGORIES}
    })

if __name__ == '__main__':
    os.makedirs('static/classifier', exist_ok=True)
    app.run(debug=True, port=5002, host='0.0.0.0')
