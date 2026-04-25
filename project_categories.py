"""
Tech Project Category Dictionary — Dev Tool Buying-Signal Classifier (v2)
==========================================================================

27 categories across 6 domains. Every category maps to a concrete dev-tool
BUYING MOTION (a vendor wedge), not just an engineering activity.

What changed in v2:
  - Sharpened every category around the named buyer_signals — if a tool's
    buyer wouldn't reasonably appear here, the slug is gone.
  - Added `co_occurrence_required`: structured rules that the engine now
    enforces (noise-note rules that v1 only described in English).
  - Added `slug_ownership` priority resolution: when a slug like
    `kubernetes` qualifies for A1, A4, and B3, only the highest-priority
    category gets credit per job.
  - Fixed bugs: priority collision (D3/E1), react-native duplication in E4,
    docstring count, weighted min_jobs threshold drift.
  - Tightened C3 (LLM) to AI APPLICATION BUILDERS only (LangSmith / Pinecone
    buyers), removed crowdwork-leaning slugs.
  - Tightened C6 (BI) to dev-tool-flavored BI (Hex/Lightdash/Cube/Metabase),
    moved tableau/power-bi to supporting with co-occurrence required.
  - Tightened E5 (Dev Productivity) — removed jira/confluence/pull-request
    from supporting (too universal); kept AI-coding + monorepo signature.
  - Rebuilt A3 (FinOps) with kubernetes+cost co-occurrence — was effectively
    dead in v1 (2 hits) due to over-narrow slugs.
  - Tightened A5 (Migration) to migration-TOOLING buyers, not consultancies.

Usage:
    from project_categories import classify_company, CATEGORIES
    results = classify_company(company_name, job_entries)
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CoOccurrenceRule:
    """A slug-level co-occurrence requirement enforced by the engine.

    If `slug` matches in a job, it ONLY counts toward this category when
    at least one of `requires_any` slugs is also present in the same job
    (or a job_title_pattern matches). This is how we enforce noise notes
    as code rather than English wishes.
    """
    slug: str                              # the noisy slug we're gating
    requires_any: list[str] = field(default_factory=list)   # any one of these slugs
    or_title_match: bool = False           # OR job-title pattern matches


@dataclass
class Category:
    id: str                                # e.g. "A1"
    name: str                              # human-readable
    domain: str                            # domain label
    buyer_signals: list[str]               # vendors that target this signal
    primary_slugs: list[str]               # high-precision; 1 hit = strong
    supporting_slugs: list[str]            # medium-precision; need 2+ or co-occurrence
    job_title_patterns: list[str]          # regex (case-insensitive)
    min_jobs: int = 1                      # min RAW (unweighted) matching jobs to qualify
    priority: int = 99                     # tie-break (lower = higher priority)
    confirmed_volume: int = 0              # validated DB hits
    co_occurrence_required: list[CoOccurrenceRule] = field(default_factory=list)
    priority_reason: str = ""              # WHY this priority — documented for future-you
    noise_notes: str = ""                  # known pollution (now mostly enforced in code)

    def all_slugs(self) -> list[str]:
        return self.primary_slugs + self.supporting_slugs


# ---------------------------------------------------------------------------
# Category Definitions
# ---------------------------------------------------------------------------

CATEGORIES: list[Category] = [

    # =========================================================================
    # DOMAIN A — Cloud Infrastructure & Platform
    # =========================================================================

    Category(
        id="A1",
        name="Cloud-Native Infrastructure (K8s + IaC)",
        domain="Cloud Infrastructure & Platform",
        priority=3,
        priority_reason=(
            "Largest single dev-infra wedge. Buyers (HashiCorp, Pulumi, Spacelift, Wiz, "
            "Sysdig) sell to platform/SRE/DevOps teams. High-precision, high-volume — "
            "wins ties over generic 'developer productivity' E5."
        ),
        confirmed_volume=17_249,
        buyer_signals=[
            "Datadog", "HashiCorp", "Pulumi", "Spacelift", "env0",
            "Wiz", "Grafana Cloud", "Aqua Security", "Sysdig",
        ],
        primary_slugs=[
            "kubernetes",
            "terraform",
            "helm",
            "argocd",
            "flux",
            "kustomize",
            "crossplane",
            "pulumi",
            "infrastructure-as-code-iac",
            "gitops",
            "cilium",
            "ebpf",
            "spacelift",
            "env0",
        ],
        supporting_slugs=[
            "docker",
            "containerd",
            "ansible",
            "chef",
            "puppet",
            "saltstack",
            "container-orchestration",
            "google-kubernetes-engine",
            "amazon-elastic-kubernetes-service-amazon-eks",
            "azure-kubernetes-service",
            "multicloud",
            "hybrid-cloud",
        ],
        job_title_patterns=[
            r"(platform|infrastructure|devops|cloud|sre|site reliability|devsecops)\s+engineer",
            r"infrastructure\s+(architect|lead|manager)",
            r"kubernetes\s+(engineer|administrator|specialist)",
            r"cloud\s+(architect|engineer|infrastructure)",
            r"(devsecops|devops)\s+(lead|architect|engineer)",
        ],
        co_occurrence_required=[
            # ansible/chef/puppet appear in legacy on-prem ops too — gate them
            CoOccurrenceRule(slug="ansible", requires_any=["kubernetes", "terraform", "gitops", "helm", "argocd"], or_title_match=True),
            CoOccurrenceRule(slug="chef",    requires_any=["kubernetes", "terraform", "gitops", "helm", "argocd"], or_title_match=True),
            CoOccurrenceRule(slug="puppet",  requires_any=["kubernetes", "terraform", "gitops", "helm", "argocd"], or_title_match=True),
        ],
        noise_notes=(
            "ansible/chef/puppet appear in on-premise IT ops roles too. Engine gates them "
            "via co_occurrence_required: they only count when paired with a cloud-native "
            "primary slug or a relevant job title."
        ),
    ),

    Category(
        id="A2",
        name="CI/CD Pipeline & Release Automation",
        domain="Cloud Infrastructure & Platform",
        priority=6,
        priority_reason=(
            "Distinct buyer (Harness, Codefresh, JFrog, Octopus). Beats E5 because it has "
            "specific tool slugs; defers to A1/B3 when build/release lives inside a broader "
            "platform-eng remit."
        ),
        confirmed_volume=19_633,
        buyer_signals=[
            "GitHub Actions", "CircleCI", "Buildkite", "Harness",
            "Argo CD", "Codefresh", "JFrog", "Octopus Deploy",
        ],
        primary_slugs=[
            "github-actions",
            "gitlab-ci",
            "jenkins",
            "circleci",
            "buildkite",
            "tekton",
            "spinnaker",
            "codefresh",
            "travis-ci",
            "teamcity",
            "bamboo",
            "harness",
            "octopus-deploy",
            "jfrog",
            "artifactory",
            "argo-cd",
            "argocd-rollouts",
        ],
        supporting_slugs=[
            "ci-cd",
            "azure-devops",
            "continuous-integration",
            "continuous-delivery",
            "deployment-automation",
            "release-management",
            # slug-normalization aliases that map back to CI/CD
            "customer-intelligence-ci",     # alias for "CI"
            "cd-certificate-of-deposit",    # alias for "CD"
        ],
        job_title_patterns=[
            r"(ci/cd|cicd|devops|build|release|deployment)\s+engineer",
            r"(release|build)\s+(engineer|manager|automation)",
            r"devops\s+(engineer|architect|lead)",
            r"(platform|infrastructure)\s+engineer.*(ci|cd|pipeline)",
        ],
        noise_notes=(
            "ci-cd (4.8K) and continuous-integration (7.7K) are reliable. The two slug-alias "
            "ghosts (customer-intelligence-ci, cd-certificate-of-deposit) are normalization "
            "artefacts that reliably back-map to CI/CD roles."
        ),
    ),

    Category(
        id="A3",
        name="Cloud Cost & FinOps",
        domain="Cloud Infrastructure & Platform",
        priority=20,
        priority_reason=(
            "Real buying motion (Kubecost, Cast.ai, Spot.io, Apptio) but slug coverage is "
            "thin — relies primarily on title regex + cloud+cost co-occurrence. Low priority "
            "so it never displaces A1/B1."
        ),
        confirmed_volume=2,
        buyer_signals=[
            "Kubecost", "Cast.ai", "Spot.io", "Apptio",
            "CloudHealth", "Harness Cloud Cost", "Infracost", "Vantage",
        ],
        primary_slugs=[
            "finops",
            "kubecost",
            "infracost",
            "cloud-cost",
            "cost-optimization",
            "cloud-billing",
            "commitment-management",
            "rightsizing",
            "vantage",
            "cast-ai",
            "spot-io",
            "apptio",
            "cloudhealth",
        ],
        supporting_slugs=[
            "aws-cost-explorer",
            "spot-instances",
            "reserved-instances",
            "cloud-economics",
            "cloud-spend",
        ],
        job_title_patterns=[
            r"(finops|cloud cost|cloud financial)\s*(engineer|analyst|manager|lead)?",
            r"cloud\s+(cost|spend|economics|optimization)",
            r"infrastructure\s+cost",
            r"cloud\s+economist",
        ],
        noise_notes=(
            "v1 had 2 total hits because the buyers are tiny but real. v2 leans on title "
            "patterns. Don't expect volume — when this fires it's a high-fidelity signal."
        ),
    ),

    Category(
        id="A4",
        name="Secret & Config Management",
        domain="Cloud Infrastructure & Platform",
        priority=15,
        priority_reason=(
            "Vault/Doppler/Infisical buyer. Distinct from broader IAM (D3) — secrets is "
            "for machines/apps, IAM is for humans/workloads."
        ),
        confirmed_volume=3_888,
        buyer_signals=[
            "HashiCorp Vault", "Doppler", "Infisical",
            "AWS Secrets Manager", "1Password Secrets Automation", "Akeyless",
        ],
        primary_slugs=[
            "vault",
            "secrets-management",
            "external-secrets",
            "aws-secrets-manager",
            "doppler",
            "infisical",
            "key-management",
            "pki",
            "certificate-management",
            "akeyless",
        ],
        supporting_slugs=[
            "config-management",
            "credential-rotation",
        ],
        job_title_patterns=[
            r"(secrets?|vault|pki|certificate|key management)\s*(engineer|admin|manager)?",
            r"(platform|security|devops)\s+engineer.*(secret|vault|pki)",
        ],
        noise_notes=(
            "vault (2.5K) is the dominant signal. Removed kubernetes/iac/zero-trust from "
            "supporting — they were causing slug-overlap pollution with A1, B3, D5."
        ),
    ),

    Category(
        id="A5",
        name="Cloud Migration & Modernization Tooling",
        domain="Cloud Infrastructure & Platform",
        priority=18,
        priority_reason=(
            "Buyers are migration-TOOLING vendors (Carbonite, Zerto, AWS MAP), not "
            "consulting firms. Title patterns deliberately exclude generic 'transformation' "
            "to avoid SI/consultancy roles."
        ),
        confirmed_volume=1_499,
        buyer_signals=[
            "AWS Migration Hub", "Azure Migrate", "Carbonite Migrate",
            "Zerto", "CloudEndure", "Cloudamize",
        ],
        primary_slugs=[
            "cloud-migration",
            "application-modernization",
            "containerization",
            "mainframe",
            "cobol",
            "legacy-modernization",
            "monolith-to-microservices",
            "zerto",
            "cloudendure",
            "azure-migrate",
            "aws-migration-hub",
            "carbonite",
            "cloudamize",
        ],
        supporting_slugs=[
            "on-premise-to-cloud",
            "datacenter-exit",
            "replatforming",
            "lift-and-shift-cloud",   # the namespaced version is OK
            # NOT plain 'lift-and-shift' (879K logistics noise per v1)
        ],
        job_title_patterns=[
            r"(cloud|application|legacy|mainframe|monolith)\s*(migration|modernization)",
            r"migration\s+(architect|engineer|lead)",
            r"mainframe\s+(developer|engineer|modernization)",
        ],
        noise_notes=(
            "Bare 'lift-and-shift' slug excluded (879K, >99% logistics/HR). 'transformation' "
            "removed from title patterns — was matching SI consultancy roles."
        ),
    ),

    # =========================================================================
    # DOMAIN B — Observability & Reliability
    # =========================================================================

    Category(
        id="B1",
        name="Observability Stack Build-Out",
        domain="Observability & Reliability",
        priority=8,
        priority_reason=(
            "Datadog/Grafana/Honeycomb buying motion. Beats B4 (APM) when buyers are "
            "investing in metrics+logs+traces holistically."
        ),
        confirmed_volume=9_211,
        buyer_signals=[
            "Datadog", "Grafana Cloud", "New Relic", "Honeycomb",
            "Coralogix", "Lightstep", "Dynatrace", "Elastic Observability",
            "Chronosphere", "Better Stack",
        ],
        primary_slugs=[
            "observability",
            "prometheus",
            "grafana",
            "opentelemetry",
            "jaeger",
            "zipkin",
            "distributed-tracing",
            "loki",
            "tempo",
            "thanos",
            "cortex",
            "mimir",
            "honeycomb",
            "lightstep",
            "coralogix",
            "instana",
            "chronosphere",
            "dynatrace",
            "better-stack",
        ],
        supporting_slugs=[
            "datadog",
            "new-relic",
            "splunk",
            "elk",
            "kibana",
            "fluentd",
            "fluent-bit",
            "log-management",
            "metrics",
            "tracing",
        ],
        job_title_patterns=[
            r"(observability|monitoring|telemetry)\s+(engineer|architect|lead)",
            r"(sre|platform|devops)\s+engineer.*(observ|monitor|telem)",
            r"(grafana|prometheus|datadog|opentelemetry)\s+(engineer|admin)",
            r"logging\s+(engineer|platform|infrastructure)",
        ],
        co_occurrence_required=[
            # splunk also lives in D4 (SOC) — gate to observability context here
            CoOccurrenceRule(slug="splunk", requires_any=["observability", "prometheus", "grafana", "opentelemetry", "log-management"], or_title_match=True),
            # datadog appears in some SecOps roles too — same gate
            CoOccurrenceRule(slug="datadog", requires_any=["observability", "prometheus", "grafana", "opentelemetry"], or_title_match=True),
        ],
        noise_notes=(
            "splunk and datadog gated by co_occurrence to keep them in observability "
            "context vs. SecOps (D4). Removed cloud-infrastructure (was generic noise)."
        ),
    ),

    Category(
        id="B2",
        name="Incident Management & On-Call",
        domain="Observability & Reliability",
        priority=12,
        priority_reason=(
            "PagerDuty/incident.io/Rootly buying motion. Distinct from B1 — different "
            "buyer (response coordination, not telemetry)."
        ),
        confirmed_volume=4_673,
        buyer_signals=[
            "PagerDuty", "Opsgenie", "FireHydrant", "incident.io",
            "Rootly", "Squadcast", "Better Stack Uptime",
        ],
        primary_slugs=[
            "pagerduty",
            "opsgenie",
            "victorops",
            "squadcast",
            "firehydrant",
            "rootly",
            "incident-io",
            "better-stack-uptime",
            "on-call",
            "slo",
            "error-budget",
            "runbooks",
            "postmortem",
            "toil-reduction",
        ],
        supporting_slugs=[
            "incident-management",
            "alert-routing",
            "escalation-policy",
            "site-reliability-engineering-sre",
        ],
        job_title_patterns=[
            r"(incident|on.call|oncall)\s+(manager|engineer|coordinator|responder)",
            r"(sre|reliability)\s+engineer",
            r"production\s+(engineer|support|operations)",
        ],
        co_occurrence_required=[
            # incident-response (4.4K) is heavy in SecOps — only count here if paired
            # with an SRE/on-call signal
            CoOccurrenceRule(slug="incident-response", requires_any=["on-call", "slo", "pagerduty", "opsgenie", "site-reliability-engineering-sre", "postmortem"], or_title_match=True),
        ],
        noise_notes=(
            "incident-response (4.4K) is now gated by co-occurrence — was the biggest "
            "B2/D4 cross-pollution source in v1."
        ),
    ),

    Category(
        id="B3",
        name="SRE / Internal Developer Platform",
        domain="Observability & Reliability",
        priority=2,
        priority_reason=(
            "Backstage/Port/OpsLevel/Cortex buying motion. Highest priority because IDP "
            "buyers are platform-engineering teams — extremely specific buyer profile, "
            "rarely confused with anything else."
        ),
        confirmed_volume=1_042,
        buyer_signals=[
            "Backstage (Spotify)", "Port", "Cortex", "OpsLevel",
            "Humanitec", "Kratix", "Roadie",
        ],
        primary_slugs=[
            "site-reliability-engineering-sre",
            "platform-engineering",
            "internal-developer-platform",
            "developer-portal",
            "service-catalog",
            "backstage",
            "golden-path",
            "paved-road",
            "humanitec",
            "kratix",
            "opslevel",
            "cortex-platform",  # disambiguated from grafana cortex
            "roadie",
        ],
        supporting_slugs=[
            "production-readiness",
            "runbook-automation",
            "developer-experience",
            "dora-metrics",
        ],
        job_title_patterns=[
            r"(platform|sre|site reliability)\s+engineer",
            r"(internal\s+developer\s+platform|idp)\s+(engineer|lead|architect)",
            r"developer\s+(platform|experience|productivity|enablement)\s+(engineer|lead|manager)",
            r"(engineering|devops)\s+platform\s+(engineer|lead|architect)",
            r"staff\s+(platform|infrastructure|devops)\s+engineer",
            r"principal\s+(platform|infrastructure|devops)\s+engineer",
        ],
        co_occurrence_required=[
            # developer-experience (226) appears in product/UX roles — gate to infra context
            CoOccurrenceRule(slug="developer-experience", requires_any=["site-reliability-engineering-sre", "platform-engineering", "internal-developer-platform", "kubernetes", "backstage"], or_title_match=True),
        ],
        noise_notes=(
            "Removed kubernetes/gitops/iac from supporting — they belong to A1 by ownership "
            "rule (see slug_owner_priority below). developer-experience is gated."
        ),
    ),

    Category(
        id="B4",
        name="Application Performance Monitoring",
        domain="Observability & Reliability",
        priority=11,
        priority_reason=(
            "Sentry/AppDynamics/Bugsnag buying motion. Narrower than B1 — app-tier error "
            "tracking specifically, not full-stack observability."
        ),
        confirmed_volume=622,
        buyer_signals=[
            "Sentry", "Bugsnag", "Rollbar", "Raygun",
            "AppDynamics", "Elastic APM", "New Relic APM",
        ],
        primary_slugs=[
            "appdynamics",
            "sentry",
            "bugsnag",
            "rollbar",
            "raygun",
            "elastic-apm",
            "apm",
            "application-performance-monitoring",
            "continuous-profiling",
            "pyroscope",
            "synthetic-monitoring",
        ],
        supporting_slugs=[
            "uptime-monitoring",
            "real-user-monitoring",
            "web-vitals",
            "performance-monitoring",
        ],
        job_title_patterns=[
            r"(apm|application performance)\s+(engineer|admin|specialist)",
            r"(error tracking|error monitoring)\s+(engineer|admin)",
            r"(sentry|appdynamics|bugsnag)\s+(admin|engineer|implementation)",
        ],
        noise_notes=(
            "sentry (335) dominates. dynatrace moved to B1 by slug-owner rule "
            "(it's broader observability than APM-specific)."
        ),
    ),

    # =========================================================================
    # DOMAIN C — Data & AI Engineering
    # =========================================================================

    Category(
        id="C1",
        name="Modern Data Stack (Warehouse + Transformation)",
        domain="Data & AI Engineering",
        priority=5,
        priority_reason=(
            "Snowflake/Databricks/dbt/Fivetran buying motion. Highest-volume data "
            "category and very specific buyer."
        ),
        confirmed_volume=17_805,
        buyer_signals=[
            "Snowflake", "Databricks", "dbt Cloud", "Fivetran",
            "Airbyte", "Hightouch", "Census", "RudderStack",
        ],
        primary_slugs=[
            "snowflake",
            "databricks",
            "dbt",
            "apache-iceberg",
            "delta-lake",
            "fivetran",
            "airbyte",
            "prefect",
            "dagster",
            "meltano",
            "data-lakehouse",
            "hightouch",
            "census",
            "rudderstack",
        ],
        supporting_slugs=[
            "airflow",
            "apache-airflow",
            "data-warehouse",
            "data-lake",
            "data-pipeline",
            "data-transformation",
            "etl",
            "elt",
            "apache-spark",
            "spark",
            "amazon-redshift",
            "google-bigquery",
            "reverse-etl",
        ],
        job_title_patterns=[
            r"(data|analytics)\s+engineer",
            r"(data|analytics)\s+(architect|platform|infrastructure)",
            r"(dataops|data ops)\s+(engineer|lead)",
            r"(snowflake|databricks|dbt)\s+(engineer|developer|architect)",
            r"(etl|elt|data pipeline)\s+(engineer|developer|architect)",
        ],
        co_occurrence_required=[
            # spark/hadoop/hive generic — gate to data-platform context
            CoOccurrenceRule(slug="spark",  requires_any=["snowflake", "databricks", "dbt", "airflow", "data-lake", "data-warehouse"], or_title_match=True),
            CoOccurrenceRule(slug="hadoop", requires_any=["snowflake", "databricks", "dbt", "airflow", "data-lake", "data-warehouse"], or_title_match=True),
        ],
        noise_notes=(
            "Added Hightouch/Census/RudderStack — reverse-ETL is a real adjacent buyer. "
            "Removed bare 'hive' and gated 'spark/hadoop'."
        ),
    ),

    Category(
        id="C2",
        name="Real-Time Streaming & Event Architecture",
        domain="Data & AI Engineering",
        priority=14,
        priority_reason=(
            "Confluent/Redpanda/Decodable buying motion. Distinct from F1 (iPaaS) — "
            "streaming is producer/consumer infra, iPaaS is enterprise SaaS glue."
        ),
        confirmed_volume=5_639,
        buyer_signals=[
            "Confluent", "Redpanda", "Decodable", "Estuary",
            "Ably", "AWS Kinesis", "Google Pub/Sub", "Aiven",
        ],
        primary_slugs=[
            "kafka",
            "apache-kafka",
            "confluent",
            "flink",
            "apache-flink",
            "redpanda",
            "event-streaming",
            "stream-processing",
            "kinesis",
            "pubsub",
            "cdc",
            "change-data-capture",
            "decodable",
            "estuary",
            "ably",
            "aiven",
            "google-pubsub",
        ],
        supporting_slugs=[
            "rabbitmq",
            "nats",
            "pulsar",
            "spark-streaming",
            "real-time-analytics",
            "azure-event-hub",
            "amazon-sqs",
            "amazon-sns",
        ],
        job_title_patterns=[
            r"(streaming|stream processing|real.?time|event.?driven)\s+(engineer|architect|developer)",
            r"(kafka|flink|kinesis|confluent)\s+(engineer|developer|admin)",
            r"data\s+engineer.*(kafka|streaming|real.?time)",
        ],
        co_occurrence_required=[
            # rabbitmq/nats/sqs/sns appear in generic backend — gate to streaming context
            CoOccurrenceRule(slug="rabbitmq",   requires_any=["kafka", "stream-processing", "event-streaming", "cdc", "flink"], or_title_match=True),
            CoOccurrenceRule(slug="nats",       requires_any=["kafka", "stream-processing", "event-streaming", "cdc", "flink"], or_title_match=True),
            CoOccurrenceRule(slug="amazon-sqs", requires_any=["kafka", "stream-processing", "event-streaming", "cdc", "flink"], or_title_match=True),
            CoOccurrenceRule(slug="amazon-sns", requires_any=["kafka", "stream-processing", "event-streaming", "cdc", "flink"], or_title_match=True),
        ],
        noise_notes=(
            "rabbitmq/nats/sqs/sns are now gated to streaming context — was C2/F1 "
            "cross-pollution source in v1."
        ),
    ),

    Category(
        id="C3",
        name="LLM Application Engineering (AI App Builders)",
        domain="Data & AI Engineering",
        priority=1,
        priority_reason=(
            "Highest priority. Buyers (LangSmith, Pinecone, Modal, Replicate, Anyscale, "
            "Together AI) target a specific builder profile. Tightened in v2 to APP "
            "BUILDERS only — removed crowdwork-prone slugs (NLP/embeddings/text-generation) "
            "that were polluting C3 with annotator/rater roles."
        ),
        confirmed_volume=9_283,
        buyer_signals=[
            "LangSmith", "Langfuse", "Pinecone", "Weaviate", "Qdrant",
            "Modal", "Replicate", "Together AI", "Anyscale", "Anthropic",
            "OpenAI", "Cohere",
        ],
        primary_slugs=[
            "large-language-model-llm",
            "langchain",
            "llamaindex",
            "langgraph",
            "langsmith",
            "langfuse",
            "retrieval-augmented-generation-rag",
            "vector-database",
            "pinecone",
            "weaviate",
            "chroma",
            "qdrant",
            "milvus",
            "llmops",
            "openai",
            "anthropic",
            "modal",
            "replicate",
            "together-ai",
            "anyscale",
            "model-context-protocol",
            "mcp",
            "cohere",
        ],
        supporting_slugs=[
            "fine-tuning",
            "prompt-engineering",
            "generative-ai",
            "hugging-face",
            "embeddings",
            "semantic-search",
            "agentic-workflow",
            "tool-calling",
            "function-calling",
        ],
        job_title_patterns=[
            r"(llm|genai|generative ai)\s+(engineer|developer|architect|platform)",
            r"(prompt|ai application|ai platform)\s+engineer",
            r"(rag|retrieval|llm)\s+(engineer|specialist|developer)",
            r"(ai|ml)\s+(infrastructure|platform)\s+engineer",
            r"applied\s+(ai|ml)\s+engineer",
            r"agent\s+engineer",
        ],
        co_occurrence_required=[
            # prompt-engineering (2.2K) appears in non-builder roles — gate it
            CoOccurrenceRule(slug="prompt-engineering", requires_any=["langchain", "llamaindex", "openai", "anthropic", "vector-database", "rag"], or_title_match=True),
            # 'transformers' / 'bert' / 'gpt' generic — removed entirely vs v1
        ],
        noise_notes=(
            "EXCLUDE crowdwork titles (ai trainer, llm evaluator, data annotator, etc.) — "
            "engine handles via CROWDWORK_TITLE_PATTERNS. Removed transformers/bert/gpt/"
            "natural-language-processing/text-generation/conversational-ai from supporting "
            "— too many false positives from research/annotation roles."
        ),
    ),

    Category(
        id="C4",
        name="MLOps & Model Lifecycle",
        domain="Data & AI Engineering",
        priority=7,
        priority_reason=(
            "MLflow/W&B/Comet/Neptune buying motion. Distinct from C3 (LLM app builders) "
            "— C4 is classical ML training/serving, C3 is LLM-app engineering."
        ),
        confirmed_volume=2_671,
        buyer_signals=[
            "MLflow", "Weights & Biases", "Comet", "Neptune.ai",
            "BentoML", "Kubeflow", "SageMaker", "Vertex AI",
        ],
        primary_slugs=[
            "mlflow",
            "kubeflow",
            "bentoml",
            "triton-inference-server",
            "feature-store",
            "feast",
            "model-registry",
            "model-serving",
            "model-deployment",
            "model-monitoring",
            "experiment-tracking",
            "data-versioning",
            "dvc",
            "vertex-ai",
            "amazon-sagemaker",
            "azure-ml",
            "weights-and-biases",
            "wandb",
            "comet-ml",
            "neptune-ai",
        ],
        supporting_slugs=[
            "pytorch",
            "tensorflow",
            "keras",
            "jax",
            "mlops",
            "model-pipeline",
            "feature-engineering",
            "hyperparameter-tuning",
        ],
        job_title_patterns=[
            r"(mlops|ml platform|ml infrastructure)\s+(engineer|architect|lead)",
            r"(model|ml)\s+(deployment|serving|platform|ops)\s+(engineer|lead)",
            r"(machine learning)\s+(platform|infrastructure|ops)",
        ],
        co_occurrence_required=[
            # pytorch/tensorflow alone = research roles, not MLOps buyers
            CoOccurrenceRule(slug="pytorch",    requires_any=["mlflow", "kubeflow", "model-serving", "model-deployment", "feature-store", "mlops"], or_title_match=True),
            CoOccurrenceRule(slug="tensorflow", requires_any=["mlflow", "kubeflow", "model-serving", "model-deployment", "feature-store", "mlops"], or_title_match=True),
        ],
        noise_notes=(
            "pytorch/tensorflow gated — alone they signal research, not MLOps tool buyers."
        ),
    ),

    Category(
        id="C5",
        name="Data Quality & Observability",
        domain="Data & AI Engineering",
        priority=16,
        priority_reason=(
            "Monte Carlo/Soda/Atlan/Collibra buying motion. Cleanly distinct from C1 "
            "(modern data stack) — different buyer (governance/lineage/quality vs "
            "ingestion/transformation)."
        ),
        confirmed_volume=13_664,
        buyer_signals=[
            "Monte Carlo", "Soda", "Great Expectations", "Anomalo",
            "Collibra", "Atlan", "DataHub", "Alation",
        ],
        primary_slugs=[
            "monte-carlo",
            "soda",
            "great-expectations",
            "anomalo",
            "data-observability",
            "data-lineage",
            "data-catalog",
            "data-governance",
            "collibra",
            "alation",
            "atlan",
            "datahub",
            "apache-atlas",
            "data-mesh",
            "data-contract",
            "data-product",
        ],
        supporting_slugs=[
            "data-quality",
            "schema-registry",
            "metadata-management",
            "data-stewardship",
            "data-reliability",
        ],
        job_title_patterns=[
            r"(data quality|data governance|data catalog|data observability)\s+(engineer|analyst|manager|steward|lead)",
            r"(data reliability|data platform)\s+engineer",
            r"(collibra|atlan|datahub|alation)\s+(admin|engineer|architect)",
        ],
        min_jobs=2,
        co_occurrence_required=[
            # data-quality (7.7K) is heavy in manufacturing/food/pharma QC
            CoOccurrenceRule(slug="data-quality",     requires_any=["monte-carlo", "soda", "great-expectations", "data-lineage", "data-catalog", "snowflake", "databricks", "dbt"], or_title_match=True),
            CoOccurrenceRule(slug="data-governance",  requires_any=["collibra", "atlan", "datahub", "data-lineage", "data-catalog", "snowflake", "databricks"], or_title_match=True),
        ],
        noise_notes=(
            "data-quality and data-governance (both >4K) are heavily gated — "
            "they're the biggest source of off-topic matches in v1 (manufacturing QC, "
            "food safety, generic compliance)."
        ),
    ),

    Category(
        id="C6",
        name="BI & Embedded Analytics",
        domain="Data & AI Engineering",
        priority=17,
        priority_reason=(
            "Dev-tool buying motion is Hex/Lightdash/Cube/Metabase/Sigma — programmable "
            "BI for engineering teams. Tableau/Power BI moved to gated supporting because "
            "their buyer is end-user analyst, not dev-tool buyer."
        ),
        confirmed_volume=101_793,  # mostly noise — see notes
        buyer_signals=[
            "Hex", "Lightdash", "Cube", "Metabase",
            "Sigma", "Sourcegraph Code Insights", "Looker", "Thoughtspot",
        ],
        primary_slugs=[
            "looker",
            "sigma",
            "hex",
            "lightdash",
            "cube",
            "metabase",
            "superset",
            "redash",
            "thoughtspot",
            "embedded-analytics",
        ],
        supporting_slugs=[
            "tableau",
            "power-bi",
            "data-visualization",
            "self-service-analytics",
        ],
        job_title_patterns=[
            r"(analytics)\s+engineer",
            r"(bi|business intelligence)\s+(engineer|developer|architect)",
            r"(looker|metabase|superset|hex)\s+(developer|admin|engineer)",
            r"(data|analytics)\s+platform\s+(engineer|developer)",
            r"embedded\s+analytics\s+(engineer|developer)",
        ],
        min_jobs=3,
        co_occurrence_required=[
            # tableau/power-bi alone = analyst roles, not dev-tool buyers
            CoOccurrenceRule(slug="tableau",  requires_any=["dbt", "snowflake", "databricks", "looker", "hex", "metabase", "embedded-analytics"], or_title_match=True),
            CoOccurrenceRule(slug="power-bi", requires_any=["dbt", "snowflake", "databricks", "azure", "embedded-analytics"], or_title_match=True),
        ],
        noise_notes=(
            "EXCLUDED 'mode' slug entirely (24K — almost all matching the English word). "
            "tableau (18K) and power-bi (45K) gated to require co-occurrence with a "
            "data-stack slug. The 101K confirmed_volume is mostly v1 noise — expect "
            "much lower clean volume in v2."
        ),
    ),

    # =========================================================================
    # DOMAIN D — Security Engineering
    # =========================================================================

    Category(
        id="D1",
        name="AppSec & Shift-Left Security",
        domain="Security Engineering",
        priority=4,
        priority_reason=(
            "Snyk/Semgrep/Checkmarx/Veracode/SonarQube buying motion. Specific buyer "
            "(AppSec/DevSecOps engineer) and specific tools."
        ),
        confirmed_volume=6_056,
        buyer_signals=[
            "Snyk", "Checkmarx", "Veracode", "Semgrep",
            "GitHub Advanced Security", "SonarQube", "Mend", "Endor Labs",
        ],
        primary_slugs=[
            "devsecops",
            "sonarqube",
            "snyk",
            "checkmarx",
            "veracode",
            "semgrep",
            "sast",
            "static-application-security-testing-sast",
            "dast",
            "supply-chain-security",
            "sbom",
            "container-security",
            "trivy",
            "aqua",
            "anchore",
            "grype",
            "burpsuite",
            "endor-labs",
            "mend",
            "github-advanced-security",
        ],
        supporting_slugs=[
            "application-security",
            "web-application-security",
            "open-web-application-security-project-owasp",
            "vulnerability-scanning",
            "code-review",
            "secure-code-review",
        ],
        job_title_patterns=[
            r"(appsec|application security|devsecops|shift.?left)\s*(engineer|architect|analyst|lead)?",
            r"(security|appsec)\s+engineer.*(app|dev|code|software)",
            r"(sast|dast|code|software)\s+(security|scanning|testing)\s+engineer",
            r"product\s+security\s+engineer",
            r"(snyk|sonarqube|checkmarx|veracode|semgrep)\s+(admin|engineer|specialist)",
        ],
        co_occurrence_required=[
            # vuln-mgmt and pentesting overlap with D4 — gate to AppSec context
            CoOccurrenceRule(slug="vulnerability-management", requires_any=["snyk", "veracode", "semgrep", "sast", "dast", "devsecops"], or_title_match=True),
            CoOccurrenceRule(slug="penetration-testing",     requires_any=["snyk", "veracode", "semgrep", "sast", "dast", "devsecops"], or_title_match=True),
        ],
        noise_notes=(
            "Removed nessus/qualys/rapid7/zap from supporting — these belong to D4 "
            "(SecOps) by ownership rule. Gated vuln-mgmt and pentesting."
        ),
    ),

    Category(
        id="D2",
        name="Cloud Security Posture (CSPM / CNAPP)",
        domain="Security Engineering",
        priority=9,
        priority_reason=(
            "Wiz/Orca/Lacework/Sysdig buying motion. Cloud-native security — distinct "
            "from D1 (code-time) and D4 (runtime/SOC)."
        ),
        confirmed_volume=1_523,
        buyer_signals=[
            "Wiz", "Orca Security", "Lacework", "Prisma Cloud",
            "Aqua Security", "Sysdig", "Ermetic", "Upwind",
        ],
        primary_slugs=[
            "wiz",
            "orca",
            "lacework",
            "prisma-cloud",
            "cspm",
            "cnapp",
            "kubernetes-security",
            "runtime-security",
            "falco",
            "policy-as-code",
            "opa",
            "kyverno",
            "sysdig",
            "ermetic",
            "aqua-security",
            "upwind",
        ],
        supporting_slugs=[
            "cloud-security",
            "cloud-compliance",
            "cloud-native-security",
            "admission-controller",
            "security-posture",
            "misconfiguration",
            "infrastructure-security",
            "information-security",
            "cybersecurity",
            "security-engineering",
            "aws-security",
            "azure-security",
            "gcp-security",
            "cloud-security-posture",
        ],
        job_title_patterns=[
            r"(cloud security|cnapp|cspm|cloud native security)\s*(engineer|architect|analyst|lead)?",
            r"(security|cloud)\s+engineer.*(cloud|posture|cnapp|cspm)",
            r"(wiz|prisma|lacework|orca|sysdig)\s+(admin|engineer|implementation)",
            r"cloud\s+security\s+(engineer|architect|analyst|manager|lead)",
        ],
        noise_notes=(
            "Added cloud-security, information-security, cybersecurity to supporting_slugs "
            "so cloud security companies (wiz.io etc.) can be detected from their own job posts. "
            "Removed dead co_occurrence_required for cloud-security (was never indexed)."
        ),
    ),

    Category(
        id="D3",
        name="Identity & Access Management",
        domain="Security Engineering",
        priority=10,
        priority_reason=(
            "Okta/Auth0/WorkOS/Clerk/CyberArk buying motion. Distinct buyer from A4 "
            "(secrets/machines) — D3 is identity for humans/users."
        ),
        confirmed_volume=11_934,
        buyer_signals=[
            "Okta", "Auth0", "WorkOS", "Clerk",
            "CyberArk", "BeyondTrust", "Ping Identity", "Stytch",
        ],
        primary_slugs=[
            "okta",
            "auth0",
            "workos",
            "clerk",
            "stytch",
            "ping-identity",
            "cyberark",
            "beyondtrust",
            "privileged-access-management",
            "identity-and-access-management",
            "single-sign-on",
            "saml",
            "oauth2",
            "openid-connect",
            "oidc",
            "mfa",
        ],
        supporting_slugs=[
            "active-directory",
            "azure-active-directory",
            "ldap",
            "oauth",
            "scim",
            "directory-services",
        ],
        job_title_patterns=[
            r"(iam|identity|access management|sso|idp|identity provider)\s*(engineer|architect|admin|analyst|lead)?",
            r"(okta|auth0|cyberark|ping identity)\s+(admin|engineer|architect)",
            r"(privileged access|pam|idm|identity management)\s+(engineer|admin|analyst)",
        ],
        min_jobs=2,
        co_occurrence_required=[
            # active-directory (7.3K) is generic Windows IT — gate to identity context
            CoOccurrenceRule(slug="active-directory",       requires_any=["okta", "auth0", "saml", "oidc", "single-sign-on", "scim", "privileged-access-management"], or_title_match=True),
            CoOccurrenceRule(slug="azure-active-directory", requires_any=["okta", "auth0", "saml", "oidc", "single-sign-on", "scim", "privileged-access-management"], or_title_match=True),
            CoOccurrenceRule(slug="ldap",                   requires_any=["okta", "auth0", "saml", "oidc", "single-sign-on", "scim"], or_title_match=True),
        ],
        noise_notes=(
            "active-directory was the biggest D3 polluter in v1 (7.3K, mostly Windows IT "
            "ops). Now strictly gated. Added Stytch."
        ),
    ),

    Category(
        id="D4",
        name="Security Operations (SOC / SIEM / SOAR)",
        domain="Security Engineering",
        priority=13,
        priority_reason=(
            "Splunk/CrowdStrike/SentinelOne/Torq/Swimlane buying motion. Threat detection "
            "and response, distinct from D1 (code) and D2 (cloud posture)."
        ),
        confirmed_volume=3_253,
        buyer_signals=[
            "Splunk", "CrowdStrike", "SentinelOne", "Elastic Security",
            "Chronicle", "Torq", "Swimlane", "Tines",
        ],
        primary_slugs=[
            "crowdstrike",
            "sentinelone",
            "splunk",
            "security-information-and-event-management-siem",
            "soar",
            "soc",
            "threat-intelligence",
            "threat-hunting",
            "edr",
            "xdr",
            "malware-analysis",
            "forensics",
            "red-team",
            "chronicle",
            "microsoft-defender",
            "torq",
            "swimlane",
            "tines",
            "splunk-es",
            "elastic-security",
        ],
        supporting_slugs=[
            "incident-response",
            "vulnerability-management",
            "penetration-testing",
            "nessus",
            "qualys",
            "rapid7",
            "zap",
            "security-operations",
            "cyber-threat-intelligence",
            "siem",
        ],
        job_title_patterns=[
            r"(soc|security operations|siem|soar)\s*(analyst|engineer|manager|lead|architect)?",
            r"(threat)\s+(analyst|hunter|researcher|intelligence)",
            r"(incident response|forensics|malware)\s+(analyst|engineer|responder)",
            r"(red team|blue team|purple team)\s+(analyst|engineer|lead)",
            r"(crowdstrike|sentinelone|defender)\s+(admin|engineer|analyst)",
        ],
        noise_notes=(
            "Added Torq/Swimlane/Tines (SOAR vendors that were missing from v1). "
            "vuln-mgmt and pentesting now belong here primarily — D1 has co-occurrence "
            "gates for them so they don't cross-pollinate."
        ),
    ),

    Category(
        id="D5",
        name="Zero Trust & Network Security",
        domain="Security Engineering",
        priority=19,
        priority_reason=(
            "Tailscale/Cloudflare Access/Zscaler/Twingate/Palo Alto buying motion. Network "
            "perimeter / SASE / ZTNA — distinct from D3 (identity) and D2 (cloud posture)."
        ),
        confirmed_volume=5_631,
        buyer_signals=[
            "Cloudflare Access", "Tailscale", "Zscaler",
            "Twingate", "Palo Alto Networks", "Fortinet", "NetSkope",
        ],
        primary_slugs=[
            "zero-trust",
            "ztna",
            "microsegmentation",
            "tailscale",
            "zscaler",
            "twingate",
            "netskope",
            "sase",
            "palo-alto-networks",
            "fortinet",
        ],
        supporting_slugs=[
            "service-mesh",
            "istio",
            "linkerd",
            "envoy",
            "vpn",
            "network-security",
            "firewall",
            "intrusion-detection",
            "ddos-protection",
            "cloudflare",
        ],
        job_title_patterns=[
            r"(zero trust|ztna|network security|sase)\s*(engineer|architect|analyst|admin)?",
            r"(network|security)\s+engineer.*(zero.?trust|ztna|micro.?segmentation)",
            r"(cloudflare|zscaler|tailscale|twingate)\s+(admin|engineer|architect)",
        ],
        co_occurrence_required=[
            # vpn (2.2K) is heavily IT-ops/remote-work — gate to security context
            CoOccurrenceRule(slug="vpn",   requires_any=["zero-trust", "ztna", "sase", "tailscale", "zscaler", "twingate", "firewall"], or_title_match=True),
            # envoy is also a microservices proxy — gate
            CoOccurrenceRule(slug="envoy", requires_any=["zero-trust", "service-mesh", "istio", "linkerd", "microsegmentation"], or_title_match=True),
            # cloudflare is broad — gate to security context here
            CoOccurrenceRule(slug="cloudflare", requires_any=["zero-trust", "ztna", "sase", "tailscale", "zscaler", "twingate", "firewall", "ddos-protection"], or_title_match=True),
        ],
        noise_notes=(
            "Added Palo Alto / Fortinet / NetSkope (missing from v1 buyer roundtrip). "
            "vpn/envoy/cloudflare gated. zero-trust no longer in A4 (was 3-way overlap)."
        ),
    ),

    # =========================================================================
    # DOMAIN E — Software Development Lifecycle
    # =========================================================================

    Category(
        id="E1",
        name="Test Automation & Quality Engineering",
        domain="Software Development Lifecycle",
        priority=21,  # was 10, collided with D3 — moved
        priority_reason=(
            "Sauce Labs/BrowserStack/mabl/Cypress buying motion. Tightened in v2 — "
            "REQUIRES a specific tool slug, not just 'quality-assurance' (37.6K, mostly "
            "manufacturing/food/healthcare QC)."
        ),
        confirmed_volume=12_124,
        buyer_signals=[
            "Sauce Labs", "BrowserStack", "mabl", "Testim",
            "Applitools", "Percy", "Chromatic", "k6",
        ],
        primary_slugs=[
            "cypress",
            "playwright",
            "selenium",
            "puppeteer",
            "appium",
            "jest",
            "pytest",
            "junit",
            "testng",
            "vitest",
            "mocha",
            "k6",
            "jmeter",
            "gatling",
            "locust",
            "test-automation",
            "visual-testing",
            "percy",
            "applitools",
            "chromatic",
            "contract-testing",
            "pact",
            "sauce-labs",
            "browserstack",
            "mabl",
            "testim",
            "k6-load-testing",
        ],
        supporting_slugs=[
            "load-testing",
            "performance-testing",
            "testrail",
            "zephyr",
            "quality-engineering",
            "continuous-testing",
        ],
        job_title_patterns=[
            r"(qa|sdet|qe)\s*(automation|engineer|developer|lead|architect|analyst)?",
            r"(test|testing)\s+(automation|engineer|developer|lead|architect)",
            r"(playwright|cypress|selenium|jest|pytest|k6)\s+(engineer|developer|automation)",
            r"(performance|load|stress)\s+test(ing)?\s+engineer",
        ],
        co_occurrence_required=[
            # quality-assurance (37.6K) is mostly non-software — strictly gated
            # Note: 'quality-assurance' is intentionally NOT in the slug lists above;
            # it's only allowed via an ad-hoc co-occurrence check below if you choose to add it.
        ],
        noise_notes=(
            "EXCLUDED 'quality-assurance' slug entirely (37.6K, mostly manufacturing/food/"
            "healthcare/pharma QC). Engine requires at least 1 specific tool slug. "
            "jest (6.2K) alone is sufficient."
        ),
    ),

    Category(
        id="E2",
        name="API Design & Developer Platform",
        domain="Software Development Lifecycle",
        priority=22,
        priority_reason=(
            "Postman/Stoplight/Kong/Apigee/ReadMe buying motion. API-tier dev tools."
        ),
        confirmed_volume=3_065,
        buyer_signals=[
            "Postman", "Stoplight", "ReadMe", "Kong",
            "Tyk", "Ambassador", "Apigee", "Bruno",
        ],
        primary_slugs=[
            "api-design",
            "openapi",
            "swagger",
            "api-management",
            "api-gateway",
            "kong",
            "apigee",
            "tyk",
            "postman",
            "insomnia",
            "bruno",
            "api-testing",
            "api-first",
            "stoplight",
            "readme-io",
            "ambassador",
        ],
        supporting_slugs=[
            "graphql",
            "grpc",
            "rest-api",
            "api-documentation",
            "api-security",
            "rate-limiting",
            "api-versioning",
            "webhook",
        ],
        job_title_patterns=[
            r"(api|gateway)\s+(engineer|architect|developer|platform)",
            r"(platform|developer\s+experience)\s+engineer.*(api|gateway)",
            r"(postman|kong|apigee|stoplight)\s+(admin|engineer|developer)",
        ],
        co_occurrence_required=[
            # graphql/grpc/rest-api in generic backend — gate to API-platform context
            CoOccurrenceRule(slug="graphql",  requires_any=["api-design", "api-gateway", "api-management", "openapi", "kong", "apigee"], or_title_match=True),
            CoOccurrenceRule(slug="grpc",     requires_any=["api-design", "api-gateway", "api-management", "openapi", "kong", "apigee"], or_title_match=True),
            CoOccurrenceRule(slug="rest-api", requires_any=["api-design", "api-gateway", "api-management", "openapi", "kong", "apigee"], or_title_match=True),
        ],
        noise_notes=(
            "Added Bruno + ReadMe slugs (missing buyer roundtrip in v1). "
            "graphql/grpc/rest-api gated to API-platform context."
        ),
    ),

    Category(
        id="E3",
        name="Frontend Engineering & Web Platform",
        domain="Software Development Lifecycle",
        priority=23,
        priority_reason=(
            "Vercel/Netlify/Chromatic/LaunchDarkly/Split.io buying motion. Tightened in "
            "v2 — vite/react alone are too generic, gated by co-occurrence."
        ),
        confirmed_volume=14_069,
        buyer_signals=[
            "Chromatic", "Percy", "Vercel", "Netlify",
            "LaunchDarkly", "Split.io", "Cloudflare Pages", "Statsig",
        ],
        primary_slugs=[
            "storybook",
            "chromatic",
            "core-web-vitals",
            "vercel",
            "netlify",
            "launchdarkly",
            "feature-flags",
            "ab-testing",
            "design-system",
            "web-performance",
            "split-io",
            "statsig",
            "percy-io",
            "cloudflare-pages",
            "cloudflare-workers",
        ],
        supporting_slugs=[
            "react",
            "nextjs",
            "vue",
            "angular",
            "svelte",
            "typescript",
            "webpack",
            "vite",
        ],
        job_title_patterns=[
            r"(frontend|front.end|web|ui|ux)\s+(engineer|developer|architect|lead)",
            r"(react|nextjs|vue|angular|svelte)\s+(engineer|developer)",
            r"(web platform|frontend platform|ui platform)\s+(engineer|architect|lead)",
            r"(design system|component library|storybook)\s+engineer",
        ],
        co_occurrence_required=[
            # vite/react/typescript alone are everywhere — require frontend platform signal
            CoOccurrenceRule(slug="vite", requires_any=["react", "nextjs", "typescript", "webpack", "storybook", "vercel"], or_title_match=True),
        ],
        noise_notes=(
            "Added Split.io / Statsig (feature-flag adjacents) to buyer signature. "
            "vite gated to require co-occurrence with another FE tool."
        ),
    ),

    Category(
        id="E4",
        name="Mobile Engineering",
        domain="Software Development Lifecycle",
        priority=24,
        priority_reason=(
            "Bitrise/Fastlane/TestFlight/Crashlytics/Firebase buying motion. Mobile-CI "
            "and mobile-error-tracking buyers."
        ),
        confirmed_volume=9_446,
        buyer_signals=[
            "Bitrise", "TestFlight", "Firebase App Distribution",
            "Instabug", "Embrace", "Bugsnag Mobile", "RevenueCat",
        ],
        primary_slugs=[
            "flutter",
            "swift",
            "kotlin",
            "swiftui",
            "jetpack-compose",
            "react-native",
            "dart",
            "capacitor",
            "ionic",
            "xcuitest",
            "espresso",
            "fastlane",
            "bitrise",
            "crashlytics",
            "instabug",
            "embrace",
            "revenuecat",
        ],
        supporting_slugs=[
            "ios",
            "android",
            "expo",
            "firebase",
            "push-notifications",
            "mobile-analytics",
        ],
        job_title_patterns=[
            r"(ios|android|mobile|flutter|react native|swiftui)\s+(engineer|developer|architect|lead)",
            r"(swift|kotlin|dart)\s+(engineer|developer)",
            r"mobile\s+(platform|devops|release|ci/cd)\s+(engineer|lead)",
        ],
        co_occurrence_required=[
            # ios alone is broad — gate to mobile-eng context
            CoOccurrenceRule(slug="ios", requires_any=["swift", "swiftui", "xcuitest", "fastlane", "bitrise", "react-native", "flutter"], or_title_match=True),
        ],
        noise_notes=(
            "Fixed v1 bug: react-native was duplicated in primary AND supporting. "
            "Added Embrace + RevenueCat. ios gated."
        ),
    ),

    Category(
        id="E5",
        name="Developer Productivity & AI Coding",
        domain="Software Development Lifecycle",
        priority=25,
        priority_reason=(
            "Linear/Cursor/Copilot/Sourcegraph/Codeium buying motion. v2 sharpens the "
            "lens to dev-loop tooling buyers — removed jira/confluence/pull-request "
            "(those are in EVERY company, no signal). Lowest priority — never wins ties."
        ),
        confirmed_volume=65_007,  # mostly v1 noise — expect lower clean volume
        buyer_signals=[
            "Cursor", "GitHub Copilot Enterprise", "Codeium", "Sourcegraph",
            "Tabnine", "Linear", "JetBrains", "Swimm", "Aider", "Continue.dev",
        ],
        primary_slugs=[
            "cursor",
            "github-copilot",
            "codeium",
            "sourcegraph",
            "tabnine",
            "aider",
            "continue-dev",
            "claude-code",
            "linear",
            "monorepo",
            "nx",
            "turborepo",
            "bazel",
            "trunk-based-development",
            "gitpod",
            "codespaces",
            "ai-pair-programming",
            "ai-coding-assistant",
            "jetbrains",
            "intellij",
            "swimm",
        ],
        supporting_slugs=[
            "developer-productivity",
            "developer-tools",
            "technical-debt",
            "gitflow",
        ],
        job_title_patterns=[
            r"(developer|engineering|dev)\s+(productivity|experience|enablement|tooling)\s*(engineer|lead|manager)?",
            r"(tooling|platform)\s+engineer.*(developer|productivity|inner.?loop)",
            r"engineering\s+(effectiveness|enablement|experience)",
            r"(build|developer)\s+infrastructure\s+engineer",
        ],
        min_jobs=3,
        noise_notes=(
            "v2 MAJOR REWRITE. Removed jira (20K), confluence (8K), pull-request (19K), "
            "github (3.6K), gitlab (1.4K), code-review (1K), version-control (4K), notion "
            "(5.3K) — these are universal SDLC noise, not buyer signal. Added AI-coding "
            "tools (Cursor, Copilot, Codeium, Sourcegraph, Aider, Claude Code) which were "
            "v1's biggest buyer-roundtrip gap."
        ),
    ),

    # =========================================================================
    # DOMAIN F — Enterprise Integration & Storage
    # =========================================================================

    Category(
        id="F1",
        name="Integration & API Orchestration (iPaaS)",
        domain="Enterprise Integration & Storage",
        priority=26,
        priority_reason=(
            "MuleSoft/Workato/Boomi/n8n/Zapier buying motion. Distinct from C2 "
            "(streaming) — iPaaS is enterprise SaaS-to-SaaS, not data-pipeline plumbing."
        ),
        confirmed_volume=2_097,
        buyer_signals=[
            "MuleSoft", "Workato", "Boomi", "Tray.io",
            "n8n", "Zapier Enterprise", "Celigo",
        ],
        primary_slugs=[
            "mulesoft",
            "tibco",
            "biztalk",
            "workato",
            "boomi",
            "tray-io",
            "n8n",
            "ipaas",
            "enterprise-integration",
            "celigo",
            "zapier-enterprise",
        ],
        supporting_slugs=[
            "api-orchestration",
            "middleware",
            "service-oriented-architecture-soa",
        ],
        job_title_patterns=[
            r"(integration|ipaas|middleware|mulesoft|boomi)\s*(engineer|architect|developer|consultant|lead)?",
            r"(enterprise|api)\s+integration\s+(engineer|architect|developer)",
            r"(mulesoft|tibco|boomi|workato)\s+(developer|architect|consultant)",
        ],
        noise_notes=(
            "Removed message-queue/rabbitmq/sqs/sns — those belong to C2 by ownership. "
            "F1 is now strictly enterprise-iPaaS buyers."
        ),
    ),

    Category(
        id="F2",
        name="Database Engineering & Storage",
        domain="Enterprise Integration & Storage",
        priority=27,
        priority_reason=(
            "PlanetScale/Neon/CockroachDB/Supabase/Hasura/Prisma buying motion. Modern "
            "OLTP & developer-friendly DB tools."
        ),
        confirmed_volume=11_984,
        buyer_signals=[
            "PlanetScale", "Neon", "CockroachDB", "Supabase",
            "Hasura", "Prisma", "Timescale", "ClickHouse",
        ],
        primary_slugs=[
            "cockroachdb",
            "planetscale",
            "neon",
            "supabase",
            "timescaledb",
            "clickhouse",
            "trino",
            "presto",
            "neo4j",
            "database-migration",
            "schema-migration",
            "liquibase",
            "flyway",
            "query-optimization",
            "sharding",
            "replication",
            "hasura",
            "prisma",
        ],
        supporting_slugs=[
            "postgresql",
            "postgres",
            "mysql",
            "aurora",
            "dynamodb",
            "cassandra",
            "mongodb",
            "redis",
            "elasticsearch",
            "cosmosdb",
            "nosql",
            "database-administration",
        ],
        job_title_patterns=[
            r"(database|dba|dbre|db)\s*(reliability|engineer|architect|administrator|developer|lead)?",
            r"(data store|storage|database)\s+(engineer|architect|platform)",
            r"(postgresql|mysql|mongodb|cassandra|redis)\s+(dba|engineer|developer|admin)",
            r"(sql|nosql|distributed database)\s+engineer",
        ],
        co_occurrence_required=[
            # presto/elasticsearch overlap with C1/B1 — gate to DB-eng context
            CoOccurrenceRule(slug="presto",        requires_any=["query-optimization", "database-migration", "sharding", "replication"], or_title_match=True),
            CoOccurrenceRule(slug="elasticsearch", requires_any=["query-optimization", "database-migration", "sharding", "replication"], or_title_match=True),
        ],
        noise_notes=(
            "Added Hasura + Prisma. presto/elasticsearch gated to DB-eng context (vs C1/B1)."
        ),
    ),
]

# ---------------------------------------------------------------------------
# Index + lookup helpers
# ---------------------------------------------------------------------------

CATEGORY_BY_ID: dict[str, Category] = {c.id: c for c in CATEGORIES}
PRIORITY_ORDER: list[str] = [c.id for c in sorted(CATEGORIES, key=lambda c: c.priority)]

# Build slug → category map. For slugs that legitimately span categories, we use
# SLUG_OWNER_PRIORITY to give credit to ONE category per match (the winner).
SLUG_TO_CATEGORIES: dict[str, list[str]] = {}
for cat in CATEGORIES:
    for slug in cat.primary_slugs:
        SLUG_TO_CATEGORIES.setdefault(slug, []).append(cat.id)
    for slug in cat.supporting_slugs:
        SLUG_TO_CATEGORIES.setdefault(slug, []).append(cat.id)

# Slug ownership rule: when a slug matches multiple categories, the winning
# category is the one with the higher priority (lower priority NUMBER).
# This prevents double-counting (e.g., kubernetes matching A1 and B3 simultaneously).
SLUG_OWNER_PRIORITY: dict[str, str] = {}
for slug, cats in SLUG_TO_CATEGORIES.items():
    if len(cats) == 1:
        SLUG_OWNER_PRIORITY[slug] = cats[0]
    else:
        winner = min(cats, key=lambda cid: CATEGORY_BY_ID[cid].priority)
        SLUG_OWNER_PRIORITY[slug] = winner

# Compile co-occurrence rules into a fast lookup: (cat_id, slug) -> rule
CO_OCCURRENCE_INDEX: dict[tuple[str, str], CoOccurrenceRule] = {
    (cat.id, rule.slug): rule
    for cat in CATEGORIES
    for rule in cat.co_occurrence_required
}

# ---------------------------------------------------------------------------
# Crowdwork / noise exclusion patterns
# ---------------------------------------------------------------------------

CROWDWORK_TITLE_PATTERNS = re.compile(
    r"(ai trainer|llm evaluator|data annotator|content reviewer|"
    r"language specialist|ai content|rater|crowd\s*work|freelance.*ai|"
    r"ai.*freelance|annotation specialist)",
    re.IGNORECASE,
)

EXCLUDE_COMPANY_PATTERNS = re.compile(
    r"(staffing|recruiting|talent solutions|headhunter|manpower|"
    r"kelly services|adecco|randstad|robert half|hays |kforce|"
    r"tek systems|teksystems|infosys bpm|wipro|accenture|cognizant|"
    r"tata consultancy|tcs|capgemini|deloitte consulting|kpmg consulting)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Classification engine
# ---------------------------------------------------------------------------

def _co_occurrence_satisfied(rule: CoOccurrenceRule,
                              job_slugs: set[str],
                              title_matches_category: bool) -> bool:
    """A noisy slug is allowed to count only if its co-occurrence rule passes."""
    if any(req in job_slugs for req in rule.requires_any):
        return True
    if rule.or_title_match and title_matches_category:
        return True
    return False


def classify_company(
    company_name: str,
    job_entries: list[dict],   # each: {"title": str, "slugs": list[str], "days_ago": int}
    min_confidence: float = 3.0,
) -> dict:
    """
    Classify a company into one or more dev-tool buying-signal categories.

    Returns:
        {
          "primary": "A1",
          "primary_name": "...",
          "qualifying": [{"id": "A1", "name": "...", "confidence": 42.5}, ...],
          "scores": {"A1": 42.5, "C1": 18.0, ...},
          "total_jobs": 24,
          "is_excluded": False,
        }
    """
    if EXCLUDE_COMPANY_PATTERNS.search(company_name):
        return {"primary": None, "primary_name": None, "qualifying": [],
                "scores": {}, "total_jobs": 0, "is_excluded": True}

    total = len(job_entries)
    if total == 0:
        return {"primary": None, "primary_name": None, "qualifying": [],
                "scores": {}, "total_jobs": 0, "is_excluded": False}

    counts: dict[str, float] = {c.id: 0.0 for c in CATEGORIES}
    raw_counts: dict[str, int] = {c.id: 0 for c in CATEGORIES}  # for min_jobs check

    for entry in job_entries:
        title = entry.get("title", "")
        job_slugs = set(entry.get("slugs", []))
        weight = 2.0 if entry.get("days_ago", 999) <= 90 else 1.0
        is_crowdwork = bool(CROWDWORK_TITLE_PATTERNS.search(title))

        # Pre-compute title-match per category (used by co-occurrence rules)
        title_matches: dict[str, bool] = {}
        for cat in CATEGORIES:
            title_matches[cat.id] = any(
                re.search(p, title, re.IGNORECASE) for p in cat.job_title_patterns
            )

        # Apply slug-owner rule: each slug counts toward AT MOST one category
        owned_slugs_per_cat: dict[str, set[str]] = {c.id: set() for c in CATEGORIES}
        for slug in job_slugs:
            owner = SLUG_OWNER_PRIORITY.get(slug)
            if owner:
                owned_slugs_per_cat[owner].add(slug)

        for cat in CATEGORIES:
            if cat.id == "C3" and is_crowdwork:
                continue

            cat_slugs = owned_slugs_per_cat[cat.id]

            # Apply co-occurrence rules: filter out noisy slugs that don't pass
            filtered_slugs = set()
            for slug in cat_slugs:
                rule = CO_OCCURRENCE_INDEX.get((cat.id, slug))
                if rule is None:
                    filtered_slugs.add(slug)
                else:
                    if _co_occurrence_satisfied(rule, job_slugs, title_matches[cat.id]):
                        filtered_slugs.add(slug)

            primary_set = set(cat.primary_slugs)
            supporting_set = set(cat.supporting_slugs)

            primary_hit = bool(filtered_slugs & primary_set)
            supporting_hits = len(filtered_slugs & supporting_set)
            title_match = title_matches[cat.id]

            qualifies = (
                primary_hit
                or supporting_hits >= 2
                or (supporting_hits >= 1 and title_match)
            )

            if qualifies:
                counts[cat.id] += weight
                raw_counts[cat.id] += 1

    # Confidence scoring — use raw total (no inflation) so percentages are accurate
    scores = {
        cat.id: round(min(100.0, (counts[cat.id] / total) * 100), 1)
        for cat in CATEGORIES
    }

    qualifying_ids = []
    for cat in CATEGORIES:
        # Percentage-based threshold: confidence >= min AND at least min_jobs matching
        percentage_qualifies = scores[cat.id] >= min_confidence and raw_counts[cat.id] >= cat.min_jobs
        # Absolute threshold: 3+ matching jobs is always a real signal for precise slugs
        absolute_qualifies = raw_counts[cat.id] >= 3

        if percentage_qualifies or absolute_qualifies:
            qualifying_ids.append(cat.id)

    primary_id = next((cid for cid in PRIORITY_ORDER if cid in qualifying_ids), None)

    qualifying = [
        {
            "id": cid,
            "name": CATEGORY_BY_ID[cid].name,
            "domain": CATEGORY_BY_ID[cid].domain,
            "confidence": scores[cid],
            "matching_jobs": raw_counts[cid],
        }
        for cid in sorted(qualifying_ids, key=lambda x: -scores[x])
    ]

    return {
        "primary": primary_id,
        "primary_name": CATEGORY_BY_ID[primary_id].name if primary_id else None,
        "qualifying": qualifying,
        "scores": {k: v for k, v in scores.items() if v > 0},
        "total_jobs": total,
        "is_excluded": False,
    }


# ---------------------------------------------------------------------------
# Quick summary for inspection
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"{'ID':<4} {'Pri':<4} {'Category':<55} {'Vol':>8}  Top Buyers")
    print("-" * 115)
    for cat in sorted(CATEGORIES, key=lambda c: c.priority):
        buyers = ", ".join(cat.buyer_signals[:3])
        print(f"{cat.id:<4} {cat.priority:<4} {cat.name:<55} {cat.confirmed_volume:>8,}  {buyers}")
    print()
    print(f"Total categories:         {len(CATEGORIES)}")
    print(f"Total slugs indexed:      {len(SLUG_TO_CATEGORIES)}")
    print(f"Slugs with multi-cat hit: "
          f"{sum(1 for cats in SLUG_TO_CATEGORIES.values() if len(cats) > 1)} "
          f"(resolved by SLUG_OWNER_PRIORITY)")
    print(f"Co-occurrence rules:      {len(CO_OCCURRENCE_INDEX)}")
