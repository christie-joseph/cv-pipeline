import re
from typing import NamedTuple, List

class TechPattern(NamedTuple):
    pattern: re.Pattern
    display: str
    category: str
    weight: float

def _compile_pattern(term: str) -> re.Pattern:
    left_b = r"\b" if re.match(r"^\w", term) else r"(?<!\w)"
    right_b = r"\b" if re.search(r"\w$", term) else r"(?!\w)"
    return re.compile(f"{left_b}{re.escape(term)}{right_b}", re.IGNORECASE)

RAW_PATTERNS = [
    # Languages
    ("Python", "Python", "Languages", 1.0),
    ("Java", "Java", "Languages", 1.0),
    ("C++", "C++", "Languages", 1.0),
    ("C#", "C#", "Languages", 1.0),
    ("Go", "Go", "Languages", 1.0),
    ("Golang", "Go", "Languages", 1.0),
    ("Rust", "Rust", "Languages", 1.0),
    ("TypeScript", "TypeScript", "Languages", 1.0),
    ("JavaScript", "JavaScript", "Languages", 1.0),
    ("SQL", "SQL", "Languages", 1.0),
    ("Bash", "Bash", "Languages", 0.9),
    ("Shell", "Bash", "Languages", 0.8),
    ("Kotlin", "Kotlin", "Languages", 1.0),
    ("Swift", "Swift", "Languages", 1.0),
    ("Ruby", "Ruby", "Languages", 1.0),
    ("Scala", "Scala", "Languages", 1.0),
    ("PHP", "PHP", "Languages", 0.9),

    # Frameworks
    ("Spring Boot", "Spring Boot", "Frameworks", 1.0),
    ("SpringBoot", "Spring Boot", "Frameworks", 1.0),
    ("Spring Framework", "Spring Boot", "Frameworks", 1.0),
    ("ASP.NET Core", "ASP.NET Core", "Frameworks", 1.0),
    ("ASP.NET", "ASP.NET Core", "Frameworks", 1.0),
    (".NET Core", "ASP.NET Core", "Frameworks", 1.0),
    (".NET", "ASP.NET Core", "Frameworks", 0.9),
    ("FastAPI", "FastAPI", "Frameworks", 1.0),
    ("Django", "Django", "Frameworks", 1.0),
    ("Flask", "Flask", "Frameworks", 0.9),
    ("React", "React", "Frameworks", 1.0),
    ("React.js", "React", "Frameworks", 1.0),
    ("ReactJS", "React", "Frameworks", 1.0),
    ("Angular", "Angular", "Frameworks", 1.0),
    ("Vue", "Vue.js", "Frameworks", 1.0),
    ("Vue.js", "Vue.js", "Frameworks", 1.0),
    ("Node.js", "Node.js", "Frameworks", 1.0),
    ("NodeJS", "Node.js", "Frameworks", 1.0),
    ("Express.js", "Express", "Frameworks", 0.9),
    ("NestJS", "NestJS", "Frameworks", 1.0),
    ("Next.js", "Next.js", "Frameworks", 1.0),
    ("Svelte", "Svelte", "Frameworks", 0.9),

    # Databases & Caches
    ("PostgreSQL", "PostgreSQL", "Databases", 1.0),
    ("Postgres", "PostgreSQL", "Databases", 1.0),
    ("MySQL", "MySQL", "Databases", 0.9),
    ("MS SQL", "MS SQL", "Databases", 1.0),
    ("SQL Server", "MS SQL", "Databases", 1.0),
    ("MongoDB", "MongoDB", "Databases", 1.0),
    ("Redis", "Redis", "Databases", 1.0),
    ("Cassandra", "Cassandra", "Databases", 1.0),
    ("DynamoDB", "DynamoDB", "Databases", 1.0),
    ("Cosmos DB", "Cosmos DB", "Databases", 1.0),
    ("Elasticsearch", "Elasticsearch", "Databases", 1.0),
    ("BigQuery", "BigQuery", "Databases", 1.0),
    ("Snowflake", "Snowflake", "Databases", 1.0),

    # Cloud & Infrastructure
    ("AWS", "AWS", "Cloud", 1.0),
    ("Amazon Web Services", "AWS", "Cloud", 1.0),
    ("Azure", "Azure", "Cloud", 1.0),
    ("Microsoft Azure", "Azure", "Cloud", 1.0),
    ("GCP", "GCP", "Cloud", 1.0),
    ("Google Cloud Platform", "GCP", "Cloud", 1.0),
    ("Docker", "Docker", "Cloud", 1.0),
    ("Kubernetes", "Kubernetes", "Cloud", 1.0),
    ("K8s", "Kubernetes", "Cloud", 1.0),
    ("Terraform", "Terraform", "Cloud", 1.0),
    ("Ansible", "Ansible", "Cloud", 0.9),
    ("Linux", "Linux", "Cloud", 0.8),

    # Messaging & Streaming
    ("Kafka", "Apache Kafka", "Messaging", 1.0),
    ("Apache Kafka", "Apache Kafka", "Messaging", 1.0),
    ("Confluent Kafka", "Apache Kafka", "Messaging", 1.0),

    ("RabbitMQ", "RabbitMQ", "Messaging", 1.0),
    ("SQS", "AWS SQS", "Messaging", 0.9),
    ("SNS", "AWS SNS", "Messaging", 0.9),
    ("EventBridge", "AWS EventBridge", "Messaging", 0.9),
    ("gRPC", "gRPC", "Messaging", 1.0),
    ("GraphQL", "GraphQL", "Messaging", 1.0),
    ("REST API", "RESTful APIs", "Messaging", 0.9),
    ("RESTful APIs", "RESTful APIs", "Messaging", 0.9),
    ("REST APIs", "RESTful APIs", "Messaging", 0.9),

    # CI/CD & DevOps
    ("CI/CD", "CI/CD", "DevOps", 0.9),
    ("GitHub Actions", "GitHub Actions", "DevOps", 1.0),
    ("GitLab CI", "GitLab CI", "DevOps", 1.0),
    ("Jenkins", "Jenkins", "DevOps", 0.9),
    ("ArgoCD", "ArgoCD", "DevOps", 1.0),
    ("Git", "Git", "DevOps", 0.8),

    # Observability
    ("Prometheus", "Prometheus", "Observability", 1.0),
    ("Grafana", "Grafana", "Observability", 1.0),
    ("Datadog", "Datadog", "Observability", 1.0),
    ("OpenTelemetry", "OpenTelemetry", "Observability", 1.0),
    ("ELK", "ELK Stack", "Observability", 0.9),
    ("Splunk", "Splunk", "Observability", 0.9),

    # Architecture & Concepts
    ("Microservices", "Microservices", "Concepts", 0.9),
    ("Distributed Systems", "Distributed Systems", "Concepts", 1.0),
    ("Event-Driven Architecture", "Event-Driven Architecture", "Concepts", 1.0),
    ("Event-Driven", "Event-Driven Architecture", "Concepts", 0.9),
    ("High Availability", "High Availability", "Concepts", 0.8),
    ("Fault Tolerance", "Fault Tolerance", "Concepts", 0.8),
    ("Concurrency", "Concurrency", "Concepts", 0.8),
    ("Unit Testing", "Unit Testing", "Concepts", 0.7),
    ("TDD", "TDD", "Concepts", 0.8),
    ("System Design", "System Design", "Concepts", 0.7),
]

TECH_REGEX_PATTERNS: List[TechPattern] = [
    TechPattern(
        pattern=_compile_pattern(term),
        display=disp,
        category=cat,
        weight=wt
    )
    for term, disp, cat, wt in RAW_PATTERNS
]

WORK_DOMAIN_PATTERNS = [
    (re.compile(r"\b(zero[\s-]downtime(?: deployments?)?)\b", re.IGNORECASE), "Zero-Downtime Deployments", "DevOps", 0.8),
    (re.compile(r"\b(distributed tracing)\b", re.IGNORECASE), "Distributed Tracing", "Observability", 0.9),
    (re.compile(r"\b(event sourcing)\b", re.IGNORECASE), "Event Sourcing", "Concepts", 0.9),
    (re.compile(r"\b(cqrs)\b", re.IGNORECASE), "CQRS", "Concepts", 0.9),
    (re.compile(r"\b(service mesh)\b", re.IGNORECASE), "Service Mesh", "Cloud", 0.9),
    (re.compile(r"\b(database optimization|query optimization)\b", re.IGNORECASE), "Query Optimization", "Databases", 0.8),
    (re.compile(r"\b(rate limiting)\b", re.IGNORECASE), "Rate Limiting", "Concepts", 0.8),
    (re.compile(r"\b(api gateway)\b", re.IGNORECASE), "API Gateway", "Concepts", 0.8),
    (re.compile(r"\b(load balancing)\b", re.IGNORECASE), "Load Balancing", "Cloud", 0.8),
    (re.compile(r"\b(sla|slo|sli)\b", re.IGNORECASE), "SLAs / SLOs", "Operations", 0.7),
    (re.compile(r"\b(canary deployment|canary releases?)\b", re.IGNORECASE), "Canary Deployments", "DevOps", 0.8),
    (re.compile(r"\b(infrastructure as code|iac)\b", re.IGNORECASE), "Infrastructure as Code", "Cloud", 0.9),
    (re.compile(r"\b(stream processing)\b", re.IGNORECASE), "Stream Processing", "Messaging", 0.8),
]
