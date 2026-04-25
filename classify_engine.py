"""
Hybrid Classification Engine: Regex (Layer 1) + Claude AI (Layer 2)
"""
import os
import re
import json
import anthropic

CLAUDE_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# =============================================================================
# MASSIVELY EXPANDED 30 Tech Projects Dictionary
# =============================================================================
TECH_PROJECTS = {
    # ── Infrastructure & Cloud ───────────────────────────────────────────
    "Cloud Migration & Modernization": [
        "cloud migration", "cloud transformation", "cloud-native", "cloud native",
        "lift and shift", "replatforming", "datacenter migration", "data center migration",
        "hybrid cloud", "multi-cloud", "multicloud", "cloud adoption", "cloud readiness",
        "cloud-first", "aws migration", "azure migration", "gcp migration",
        "cloud architect", "cloud infrastructure", "cloud platform engineer",
        "migrate to cloud", "modernize infrastructure", "terraform", "pulumi",
        "infrastructure as code", "iac", "cloudformation", "bicep",
        "cloud foundation", "landing zone"
    ],
    "Microservices & Containers": [
        "kubernetes", "k8s", "docker", "containerization", "container orchestration",
        "service mesh", "istio", "linkerd", "envoy proxy", "microservices",
        "microservice architecture", "eks", "aks", "gke", "ecs", "fargate",
        "openshift", "rancher", "helm", "kustomize", "container runtime",
        "docker compose", "podman", "containerd", "cri-o", "service discovery",
        "api mesh", "sidecar proxy", "distributed systems", "container security"
    ],
    "Serverless Architecture": [
        "serverless", "aws lambda", "azure functions", "google cloud functions",
        "cloud run", "step functions", "event-driven architecture", "eda",
        "faas", "function as a service", "serverless framework", "sam cli",
        "api gateway lambda", "event bridge", "eventbridge"
    ],
    "Mainframe Modernization": [
        "mainframe modernization", "mainframe migration", "cobol", "legacy modernization",
        "legacy migration", "as/400", "iseries", "jcl", "cics", "vsam",
        "mainframe to cloud", "legacy transformation", "monolith to microservices"
    ],
    "Disaster Recovery & HA": [
        "disaster recovery", "high availability", "active-active", "active-passive",
        "failover", "business continuity", "site reliability", "sre",
        "chaos engineering", "fault tolerance", "redundancy", "rto", "rpo",
        "geo-redundant", "multi-region", "backup and recovery", "incident response"
    ],

    # ── Data & AI ────────────────────────────────────────────────────────
    "Data Warehouse & Data Lake": [
        "snowflake", "databricks", "bigquery", "redshift", "data lake", "data lakehouse",
        "data warehouse", "data mesh", "data fabric", "data platform",
        "delta lake", "iceberg", "hudi", "data catalog", "data governance",
        "dbt", "data build tool", "fivetran", "airbyte", "stitch",
        "etl", "elt", "data pipeline", "data engineering", "data ingestion",
        "synapse analytics", "azure data factory", "glue", "athena"
    ],
    "Generative AI & LLMs": [
        "generative ai", "genai", "gen ai", "llm", "large language model",
        "openai", "gpt-4", "gpt-3", "chatgpt", "claude", "anthropic",
        "langchain", "langgraph", "llamaindex", "llama index",
        "rag", "retrieval augmented generation", "prompt engineering",
        "fine-tuning", "fine tuning", "lora", "qlora", "peft",
        "vector database", "vector store", "pinecone", "weaviate", "chromadb",
        "milvus", "qdrant", "embedding", "embeddings", "transformer",
        "hugging face", "huggingface", "diffusion model", "stable diffusion",
        "copilot", "ai assistant", "ai agent", "agentic ai", "autonomous agent",
        "multi-agent", "multi agent", "mcp", "model context protocol",
        "tool calling", "function calling", "ai orchestration",
        "gemini", "mistral", "cohere", "ollama", "vllm",
        "text generation", "natural language processing", "nlp",
        "conversational ai", "chatbot", "ai safety", "guardrails",
        "responsible ai", "ai alignment"
    ],
    "MLOps & Model Deployment": [
        "mlops", "ml ops", "sagemaker", "mlflow", "kubeflow", "vertex ai",
        "model deployment", "model serving", "model monitoring", "model registry",
        "machine learning pipeline", "ml pipeline", "feature store", "feast",
        "experiment tracking", "wandb", "weights and biases", "neptune.ai",
        "bentoml", "seldon", "kserve", "triton inference", "onnx",
        "model retraining", "continuous training", "ct/cd", "a/b testing ml",
        "data drift", "model drift", "ml engineering", "ml platform"
    ],
    "Real-time Data Streaming": [
        "kafka", "apache kafka", "confluent", "flink", "apache flink",
        "real-time streaming", "stream processing", "event streaming",
        "kinesis", "amazon kinesis", "pulsar", "apache pulsar",
        "spark streaming", "structured streaming", "ksqldb",
        "real-time analytics", "cdc", "change data capture", "debezium",
        "event sourcing", "cqrs", "event-driven", "rabbitmq", "nats"
    ],
    "Big Data & BI": [
        "tableau", "looker", "power bi", "powerbi", "qlik", "sisense",
        "hadoop", "spark", "apache spark", "pyspark", "presto", "trino",
        "big data", "data visualization", "business intelligence",
        "data analytics", "analytics engineer", "analytics platform",
        "reporting", "dashboards", "metabase", "superset", "mode analytics",
        "thoughtspot", "domo", "data analyst", "data science"
    ],

    # ── Security & Identity ──────────────────────────────────────────────
    "DevSecOps & AppSec": [
        "devsecops", "appsec", "application security", "shift-left", "shift left",
        "sast", "dast", "iast", "rasp", "sonarqube", "snyk", "checkmarx",
        "fortify", "veracode", "semgrep", "codeql", "bandit",
        "software composition analysis", "sca", "vulnerability management",
        "secure coding", "owasp", "penetration testing", "pen testing",
        "bug bounty", "security champion", "threat modeling", "sdl",
        "code scanning", "secret scanning", "container scanning"
    ],
    "Zero Trust & Network Security": [
        "zero trust", "zscaler", "cloudflare", "sase", "sse",
        "secure service edge", "secure access", "network security",
        "firewall", "waf", "web application firewall", "ids", "ips",
        "intrusion detection", "intrusion prevention", "vpn",
        "microsegmentation", "nac", "network access control",
        "palo alto networks", "fortinet", "checkpoint"
    ],
    "Identity & Access Management": [
        "identity and access management", "okta", "ping identity", "auth0",
        "cyberark", "sailpoint", "privileged access", "pam",
        "single sign-on", "sso", "mfa", "multi-factor authentication",
        "oauth", "oidc", "openid connect", "saml", "scim",
        "identity governance", "iga", "access review", "rbac",
        "role-based access", "abac", "attribute-based access",
        "non-human identity", "nhi", "workload identity",
        "service account", "api key management", "secret management",
        "hashicorp vault", "vault"
    ],
    "Cloud Security (CNAPP)": [
        "cnapp", "cspm", "cwpp", "ciem", "cloud security posture",
        "wiz", "prisma cloud", "orca security", "lacework", "aqua security",
        "cloud security", "cloud workload protection", "cloud compliance",
        "security posture management", "cloud detection and response",
        "runtime protection", "agentless security", "kspm"
    ],
    "Fraud Detection & Risk": [
        "fraud detection", "fraud prevention", "anomaly detection",
        "risk modeling", "risk scoring", "anti-fraud", "aml",
        "anti-money laundering", "kyc", "know your customer",
        "transaction monitoring", "behavioral analytics",
        "financial crime", "compliance monitoring", "regtech"
    ],

    # ── Software Engineering & DevOps ────────────────────────────────────
    "CI/CD & DevOps Automation": [
        "ci/cd", "cicd", "continuous integration", "continuous delivery",
        "continuous deployment", "jenkins", "github actions", "gitlab ci",
        "circleci", "argo cd", "argocd", "tekton", "spinnaker",
        "bamboo", "azure devops", "buildkite", "drone ci",
        "gitops", "fluxcd", "flux cd", "deployment automation",
        "release engineering", "release management", "pipeline automation",
        "build engineer", "devops engineer", "platform engineering"
    ],
    "Frontend & Web Development": [
        "react.js", "reactjs", "next.js", "nextjs", "vue.js", "vuejs",
        "angular", "svelte", "nuxt", "remix", "gatsby",
        "typescript", "webpack", "vite", "tailwind", "css-in-js",
        "component library", "design system", "storybook",
        "frontend engineer", "front-end engineer", "ui engineer",
        "web application", "progressive web app", "pwa",
        "single page application", "micro-frontend", "micro frontend"
    ],
    "Mobile App Development": [
        "react native", "flutter", "swift", "swiftui", "kotlin",
        "ios development", "android development", "mobile app",
        "mobile engineer", "mobile developer", "xamarin", "maui",
        "jetpack compose", "uikit", "core data", "arkit",
        "mobile sdk", "app store", "play store", "cross-platform mobile"
    ],
    "API Platform & Integration": [
        "api gateway", "mulesoft", "apigee", "kong", "api management",
        "graphql", "rest api", "restful", "grpc", "protobuf",
        "api design", "api first", "openapi", "swagger",
        "webhook", "integration platform", "ipaas", "workato",
        "zapier", "tray.io", "boomi", "informatica",
        "middleware", "esb", "enterprise service bus"
    ],
    "Automated Testing & QA": [
        "test automation", "selenium", "cypress", "playwright", "appium",
        "qa automation", "automated testing", "testing framework",
        "jest", "mocha", "pytest", "junit", "testng",
        "performance testing", "jmeter", "k6", "gatling", "locust",
        "load testing", "stress testing", "end-to-end testing", "e2e testing",
        "integration testing", "unit testing", "bdd", "tdd",
        "cucumber", "robot framework", "quality assurance engineer"
    ],
    "Database & Storage": [
        "mongodb", "cassandra", "dynamodb", "couchdb", "couchbase",
        "postgresql", "postgres", "mysql", "mariadb", "sql server",
        "oracle database", "database migration", "database administrator",
        "redis", "memcached", "elasticsearch", "opensearch",
        "neo4j", "graph database", "timescaledb", "influxdb",
        "cockroachdb", "planetscale", "supabase", "firebase",
        "database engineer", "data modeling", "schema design"
    ],

    # ── Enterprise Apps & Business ───────────────────────────────────────
    "ERP/CRM Implementation": [
        "sap", "salesforce", "workday", "netsuite", "dynamics 365",
        "erp implementation", "crm implementation", "erp migration",
        "sap s/4hana", "sap hana", "salesforce developer",
        "salesforce administrator", "hubspot", "zoho",
        "servicenow", "jira", "confluence", "atlassian"
    ],
    "E-commerce Platform": [
        "shopify", "shopify plus", "commercetools", "magento",
        "bigcommerce", "woocommerce", "headless commerce",
        "omnichannel", "e-commerce", "ecommerce", "online marketplace",
        "product catalog", "checkout", "cart", "payment processing"
    ],
    "FinTech & Payments": [
        "stripe", "adyen", "braintree", "square", "plaid",
        "payment gateway", "payment processing", "payment infrastructure",
        "fintech", "neobank", "digital banking", "lending platform",
        "insurance tech", "insurtech", "wealth management",
        "trading platform", "cryptocurrency exchange", "defi"
    ],
    "Robotic Process Automation": [
        "rpa", "uipath", "automation anywhere", "blue prism",
        "robotic process automation", "process automation",
        "intelligent automation", "hyperautomation", "workflow automation",
        "business process automation", "bpa", "low-code automation"
    ],

    # ── Niche / Emerging Tech ────────────────────────────────────────────
    "Observability & Monitoring": [
        "observability", "datadog", "new relic", "newrelic",
        "opentelemetry", "otel", "dynatrace", "prometheus", "grafana",
        "splunk", "elastic", "elk stack", "kibana", "logstash",
        "apm", "application performance monitoring", "distributed tracing",
        "jaeger", "zipkin", "log management", "monitoring",
        "alerting", "pagerduty", "opsgenie", "incident management"
    ],
    "Network & Infrastructure Automation": [
        "sd-wan", "sdwan", "network automation", "cisco", "meraki",
        "ansible", "puppet", "chef", "saltstack",
        "arista", "juniper", "f5", "load balancer", "dns",
        "bgp", "mpls", "network engineer", "noc"
    ],
    "Edge Computing & IoT": [
        "edge computing", "iot", "internet of things", "aws iot",
        "azure iot", "google iot", "embedded systems", "embedded software",
        "firmware", "rtos", "mqtt", "lorawan", "zigbee",
        "industrial iot", "iiot", "scada", "plc",
        "connected devices", "smart devices", "wearables", "sensors"
    ],
    "Blockchain & Web3": [
        "blockchain", "web3", "smart contracts", "ethereum", "solidity",
        "cryptocurrency", "defi", "decentralized finance", "nft",
        "dao", "consensus mechanism", "hyperledger", "polygon",
        "arbitrum", "layer 2", "l2", "tokenomics",
        "crypto wallet", "dapp", "decentralized application"
    ],
    "AR/VR & Spatial Computing": [
        "augmented reality", "virtual reality", "mixed reality", "xr",
        "spatial computing", "unity3d", "unreal engine",
        "metaverse", "3d rendering", "computer vision",
        "apple vision", "visionos", "hololens", "oculus",
        "webxr", "openxr", "3d modeling"
    ],
}

# Compile regex patterns
COMPILED_PROJECTS = {}
for project, keywords in TECH_PROJECTS.items():
    pattern = r'(?i)\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
    COMPILED_PROJECTS[project] = re.compile(pattern)


def extract_excerpt(text, match, padding=80):
    start = max(0, match.start() - padding)
    end = min(len(text), match.end() + padding)
    excerpt = " ".join(text[start:end].split())
    if start > 0: excerpt = "..." + excerpt
    if end < len(text): excerpt = excerpt + "..."
    return excerpt


def classify_regex(jd_text):
    """Layer 1: Fast regex classification. Returns list of dicts."""
    results = []
    for project, pattern in COMPILED_PROJECTS.items():
        match = pattern.search(jd_text)
        if match:
            results.append({
                "project": project,
                "matched_keyword": match.group(0),
                "excerpt": extract_excerpt(jd_text, match),
                "source": "regex"
            })
    return results


def classify_claude_batch(unmatched_jds, batch_size=8):
    """
    Layer 2: Claude fallback for JDs that regex couldn't classify.
    Batches JDs together to minimize API calls.
    Returns dict mapping jd_index -> classification result.
    """
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    project_names = list(TECH_PROJECTS.keys())
    
    all_results = {}
    
    for i in range(0, len(unmatched_jds), batch_size):
        batch = unmatched_jds[i:i+batch_size]
        
        jd_blocks = []
        for idx, (jd_key, title, text) in enumerate(batch):
            # Truncate to ~800 chars to save tokens
            truncated = text[:800]
            jd_blocks.append(f"JD_{idx}:\nTitle: {title}\n{truncated}")
        
        prompt = f"""You are a tech project classifier. For each JD below, identify what tech project(s) the company is likely building.

Choose from ONLY these 30 categories (or say "Unclassified" if none fit):
{json.dumps(project_names, indent=2)}

For each JD, return JSON like:
{{"JD_0": {{"project": "category name", "summary": "1-line summary of the project"}}, "JD_1": ...}}

JDs:
{chr(10).join(jd_blocks)}

Return ONLY valid JSON, no markdown."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            resp_text = response.content[0].text
            parsed = json.loads(resp_text)
            
            for idx, (jd_key, title, text) in enumerate(batch):
                key = f"JD_{idx}"
                if key in parsed and parsed[key].get("project") != "Unclassified":
                    all_results[jd_key] = {
                        "project": parsed[key]["project"],
                        "summary": parsed[key].get("summary", ""),
                        "source": "claude"
                    }
        except Exception as e:
            print(f"Claude batch error: {e}")
            continue
    
    return all_results


def classify_domain_jobs(jobs, use_claude=True):
    """
    Main entry point. Takes list of (title, description) tuples.
    Returns structured results dict.
    """
    regex_results = []
    unmatched = []
    
    for i, (title, desc) in enumerate(jobs):
        if not desc:
            continue
        matches = classify_regex(desc)
        if matches:
            for m in matches:
                regex_results.append({
                    "job_title": title,
                    **m
                })
        else:
            unmatched.append((i, title, desc))
    
    claude_results = []
    if use_claude and unmatched:
        claude_map = classify_claude_batch(unmatched)
        for jd_key, result in claude_map.items():
            idx = jd_key
            title = unmatched[0][1]  # fallback
            for u_idx, u_title, u_desc in unmatched:
                if u_idx == idx:
                    title = u_title
                    break
            claude_results.append({
                "job_title": title,
                **result
            })
    
    return {
        "regex_results": regex_results,
        "claude_results": claude_results,
        "stats": {
            "total_jobs": len(jobs),
            "regex_matched": len(jobs) - len(unmatched),
            "unmatched_sent_to_claude": len(unmatched),
            "claude_classified": len(claude_results)
        }
    }
