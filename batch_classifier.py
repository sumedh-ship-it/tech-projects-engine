import pandas as pd
from sqlalchemy import text
from sqlalchemy import create_engine
import time

# Create ClickHouse engine
flat_data_engine = create_engine('clickhouse+http://reo_readonly_user:fghjkvbnwe4567DFGH@10.10.0.43:8123/default')

# 1. Define the 30 Tech Projects and their keyword arrays (MUST BE LOWERCASE)
TECH_PROJECTS = {
    # Infrastructure & Cloud
    "Cloud Migration": ["cloud migration", "migrating to aws", "migrating to azure", "migrating to gcp", "lift and shift", "cloud transformation", "datacenter migration"],
    "Microservices & Containers": ["kubernetes", "docker", "service mesh", "microservices architecture", "containerization", "eks", "aks", "gke", "istio"],
    "Serverless Architecture": ["serverless", "aws lambda", "azure functions", "google cloud functions", "event-driven architecture"],
    "Mainframe Modernization": ["mainframe modernization", "cobol", "legacy modernization", "legacy migration"],
    "Disaster Recovery": ["disaster recovery", "high availability", "active-active", "failover", "business continuity"],
    
    # Data & AI
    "Data Warehouse / Data Lake": ["snowflake", "databricks", "bigquery", "redshift", "data lake", "data warehouse", "data mesh"],
    "Generative AI & LLMs": ["generative ai", "genai", "llm", "large language model", "openai", "langchain", "rag", "retrieval augmented generation", "prompt engineering", "anthropic"],
    "MLOps & Model Deployment": ["mlops", "sagemaker", "mlflow", "kubeflow", "model deployment", "model monitoring", "machine learning pipeline"],
    "Real-time Data Streaming": ["kafka", "flink", "confluent", "real-time streaming", "event streaming", "kinesis"],
    "Big Data & BI": ["tableau", "looker", "powerbi", "hadoop", "spark", "big data", "data visualization", "business intelligence"],
    
    # Security & Identity
    "DevSecOps": ["devsecops", "shift-left", "shift left", "sast", "dast", "sonarqube", "snyk", "checkmarx", "fortify"],
    "Zero Trust Architecture": ["zero trust", "zscaler", "cloudflare", "sase", "sse", "secure service edge"],
    "Identity & Access Management": ["iam", "identity and access management", "okta", "ping identity", "auth0", "cyberark", "sailpoint", "privileged access"],
    "Cloud Security (CNAPP)": ["cnapp", "cspm", "cwpp", "wiz", "prisma cloud", "orca security", "lacework", "cloud security posture"],
    "Fraud & Risk Modeling": ["fraud detection", "anomaly detection", "risk modeling", "anti-fraud", "aml", "anti-money laundering"],
    
    # Software Engineering & DevOps
    "CI/CD Pipeline Automation": ["ci/cd", "continuous integration", "jenkins", "github actions", "gitlab ci", "circleci", "argo cd", "tekton"],
    "Frontend Modernization": ["react", "next.js", "vue.js", "angular", "frontend modernization", "spa", "single page application"],
    "Mobile App Development": ["react native", "flutter", "swift", "kotlin", "ios development", "android development", "mobile app"],
    "API Gateway & Management": ["api gateway", "mulesoft", "apigee", "kong", "api management", "graphql"],
    "Automated Testing & QA": ["test automation", "selenium", "cypress", "playwright", "appium", "qa automation", "automated testing"],
    "Database Migration / NoSQL": ["nosql", "mongodb", "cassandra", "dynamodb", "database migration", "redis"],
    
    # Enterprise Apps & Business
    "ERP/CRM Implementation": ["erp implementation", "crm implementation", "sap", "salesforce", "workday", "netsuite", "dynamics 365"],
    "Headless E-commerce": ["headless commerce", "shopify plus", "commercetools", "magento", "bigcommerce", "omnichannel"],
    "Payment Gateway Integration": ["stripe", "adyen", "braintree", "paypal integration", "payment gateway"],
    "Robotic Process Automation": ["rpa", "uipath", "automation anywhere", "blue prism", "robotic process automation"],
    
    # Niche / Emerging Tech
    "Observability & Telemetry": ["observability", "datadog", "new relic", "opentelemetry", "dynatrace", "prometheus", "grafana", "splunk"],
    "Network Automation (SD-WAN)": ["sd-wan", "network automation", "cisco", "meraki", "infrastructure as code", "ansible"],
    "Edge Computing & IoT": ["edge computing", "iot", "internet of things", "aws iot", "azure iot"],
    "Blockchain & Web3": ["blockchain", "web3", "smart contracts", "ethereum", "solidity", "cryptocurrency"],
    "AR/VR & Spatial Computing": ["ar/vr", "augmented reality", "virtual reality", "spatial computing", "unity", "unreal engine"]
}

def build_clickhouse_query(test_mode=True):
    """
    Builds the massive CASE WHEN query using multiMatchAny to find projects,
    then aggregates by company_domain and project name.
    """
    select_clauses = []
    
    for project_name, keywords in TECH_PROJECTS.items():
        # Escape single quotes and create regex with word boundaries
        regex_patterns = [f"\\\\b{k}\\\\b" for k in keywords]
        keyword_array_str = "['" + "','".join(regex_patterns) + "']"
        
        # ClickHouse syntax: multiMatchAny(haystack, [needles])
        condition = f"multiMatchAny(search_text, {keyword_array_str})"
        
        # Output project name if matched, else empty string
        clause = f"if({condition}, '{project_name}', '')"
        select_clauses.append(clause)
        
    # Combine them into a single array and filter out empty strings
    array_constructor = "array(" + ", ".join(select_clauses) + ")"
    filter_array = f"arrayFilter(x -> x != '', {array_constructor})"
    
    # In test mode, we limit the raw jobs BEFORE aggregation to 100,000 to keep it fast
    raw_limit_clause = "LIMIT 100000" if test_mode else ""
    
    query = f"""
    SELECT 
        company_domain,
        project_name,
        count() as job_count
    FROM (
        SELECT 
            company_domain,
            arrayJoin({filter_array}) AS project_name
        FROM (
            SELECT 
                company_domain,
                lower(job_description) AS search_text
            FROM org_jobs
            WHERE job_status = 'active' AND company_domain != '' AND company_domain != 'unknown.com'
            {raw_limit_clause}
        )
    )
    GROUP BY company_domain, project_name
    ORDER BY job_count DESC
    """
    return query

import argparse

def run_extraction(test_mode=True):
    print("Building ClickHouse aggregation query...")
    query = build_clickhouse_query(test_mode=test_mode)
    
    if test_mode:
        print("\nExecuting query on ClickHouse (scanning 100,000 jobs for test)...")
    else:
        print("\nExecuting query on ClickHouse (scanning ALL 30 MILLION jobs)...")
        print("This may take 1-3 minutes. Please wait...")
        
    start_time = time.time()
    
    with flat_data_engine.connect() as conn:
        res = conn.execute(text(query)).fetchall()
        
    duration = time.time() - start_time
    print(f"\nQuery completed in {duration:.2f} seconds.")
    print(f"Generated {len(res)} aggregated signals (Company -> Project).")
    
    # Convert to DataFrame
    df = pd.DataFrame(res, columns=["Company Domain", "Tech Project", "Job Count"])
    
    if test_mode:
        print("\nTop 20 Extracted Signals:")
        print(df.head(20).to_string(index=False))
        print("\n" + "="*80)
        print("TEST SUCCESSFUL. READY FOR 30M RUN:")
        print("To run against all 30M rows, use: python3 batch_classifier.py --full")
        print("="*80)
    else:
        # Save to CSV in full mode
        output_file = "company_tech_projects.csv"
        df.to_csv(output_file, index=False)
        print(f"\nSUCCESS! Results saved to {output_file}")
        print(f"File size: {len(df)} rows.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch classify 30M jobs into Tech Projects.")
    parser.add_argument("--full", action="store_true", help="Run against the full 30M database (default is test mode: 100k rows)")
    args = parser.parse_args()
    
    run_extraction(test_mode=not args.full)
