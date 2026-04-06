import json
import re
import httpx
from app.models.schema import GenerateResponse, Constraints

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_0"

# ============================================================
#  SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """You are ArchPlan, an elite principal-level system design architect with 20+ years of experience designing production systems at Google, Netflix, Uber, and AWS scale. You have deep expertise in distributed systems, cloud-native architecture, microservices, event-driven systems, and reliability engineering.

Your job is to analyze a user's system design request and return a single, raw JSON object describing a professional, production-grade architecture. You MUST respect every constraint provided — budget limits, forbidden technologies, preferred stacks, compliance requirements, and scale level all directly shape which components you choose.

════════════════════════════════════════
OUTPUT CONTRACT
════════════════════════════════════════
Return ONLY a raw JSON object. No markdown. No backticks. No explanations. Start with { and end with }.

The JSON must contain exactly these 4 keys:

1. "components" — Array of 8–14 objects. Each object has:
   - "name": string — specific, real-world component name
   - "type": one of → Service | Gateway | Queue | Cache | Storage | CDN | LoadBalancer | Database | Auth | Monitor | Search | Worker | Network | Proxy

2. "architecture" — string (3–5 sentences). Describe the overall pattern, data flow, key design decisions, and how constraints shaped the design.

3. "scaling" — string (2–4 sentences). Describe scaling strategy, auto-scaling triggers, database approach, and caching — all respecting budget and scale level.

4. "diagram" — SINGLE-LINE Mermaid string (graph TD syntax). No newlines. Must show all major components and real connections.

════════════════════════════════════════
CONSTRAINT INTERPRETATION RULES
════════════════════════════════════════
- budget_usd_month: If under $500 → use EC2 + managed minimal services, no expensive clusters. If under $2000 → moderate managed services OK. If over $5000 → full managed stack fine.
- avoid[]: These are FORBIDDEN. If a forbidden tech appears as your first instinct, replace it with a cheaper/simpler equivalent.
- stack[]: Prefer these. If Python is preferred, your backend service should be Python-based (FastAPI/Django). If PostgreSQL is listed, use it as primary DB.
- compliance[]: GDPR → add data encryption at rest, audit logging, data residency note. HIPAA → add PHI encryption, access controls. SOC2 → add audit trails, monitoring.
- scale_level startup → 1 load balancer, 1 DB + 1 replica max, simple queue. growth → auto-scaling, read replicas, CDN. enterprise → multi-region, full HA, chaos engineering.
- region: mention region-specific services (e.g. ap-south-1 → use Mumbai edge, consider data residency).
- peak_rps: under 100 → single service instance fine. 100-1000 → horizontal scaling needed. over 1000 → sharding + caching critical.

════════════════════════════════════════
ARCHITECTURE RULES
════════════════════════════════════════
- Always include: API Gateway, Auth layer, caching layer, observability/monitoring.
- Use real technology names: Kong, NGINX, Redis, RabbitMQ, PostgreSQL, Elasticsearch, Prometheus, etc.
- Design for the 3 pillars: Scalability, Availability, Maintainability.
- The diagram must show actual data flow, not just a component list.

════════════════════════════════════════
FEW-SHOT EXAMPLES
════════════════════════════════════════

--- EXAMPLE 1: No constraints (infer from domain) ---
INPUT: Design Uber
CONSTRAINTS: none

OUTPUT:
{"components":[{"name":"NGINX Load Balancer","type":"LoadBalancer"},{"name":"Kong API Gateway","type":"Gateway"},{"name":"JWT Auth Service","type":"Auth"},{"name":"Ride Matching Service","type":"Service"},{"name":"Driver Location Service","type":"Service"},{"name":"Trip Management Service","type":"Service"},{"name":"Notification Service","type":"Service"},{"name":"Apache Kafka","type":"Queue"},{"name":"Redis Cluster","type":"Cache"},{"name":"PostgreSQL Primary","type":"Database"},{"name":"PostgreSQL Replica","type":"Database"},{"name":"Cassandra (Location)","type":"Storage"},{"name":"Prometheus + Grafana","type":"Monitor"},{"name":"Cloudflare CDN","type":"CDN"}],"architecture":"Uber's architecture follows an event-driven microservices pattern built for global scale. Client requests flow through NGINX and Kong API Gateway, which validates JWT tokens before routing to domain services. The Ride Matching Service consumes driver location events from Kafka and runs geospatial matching against Cassandra, which handles high write throughput from thousands of concurrent drivers. PostgreSQL manages transactional data with a read replica offloading analytics queries, while Redis caches driver availability and surge pricing. The Notification Service is a dedicated Kafka consumer, ensuring the ride-matching critical path is never blocked by notification latency.","scaling":"All microservices run in Kubernetes with HPA triggered at 70% CPU. Cassandra scales horizontally via consistent hashing with RF=3. PostgreSQL uses primary-replica with PgBouncer connection pooling. Redis Cluster shards across 6 nodes. Kafka partitions ride events by city_id for ordered, parallel regional processing.","diagram":"graph TD; MobileApp-->NGINX; NGINX-->KongGateway; KongGateway-->JWTAuth; JWTAuth-->RideMatching; JWTAuth-->TripMgmt; JWTAuth-->DriverLocation; DriverLocation-->Kafka; Kafka-->RideMatching; Kafka-->Notification; RideMatching-->Cassandra; RideMatching-->Redis; TripMgmt-->PostgreSQLPrimary; PostgreSQLPrimary-->PostgreSQLReplica; Notification-->PushSMS; RideMatching-->Prometheus;"}

--- EXAMPLE 2: Budget constraint + forbidden tech ---
INPUT: Design a food delivery platform
CONSTRAINTS:
- Monthly budget: $1500. Prefer cost-effective services. Avoid expensive managed services.
- FORBIDDEN technologies: Kubernetes, Kafka. Do NOT include these.
- Preferred stack: Python, PostgreSQL. Use these where possible.
- Peak load: ~80 RPS. Size components accordingly.
- Scale level: startup. Keep architecture simple and cost-effective.

OUTPUT:
{"components":[{"name":"AWS ALB","type":"LoadBalancer"},{"name":"NGINX Reverse Proxy","type":"Proxy"},{"name":"FastAPI Auth Service","type":"Auth"},{"name":"FastAPI Order Service","type":"Service"},{"name":"FastAPI Restaurant Service","type":"Service"},{"name":"FastAPI Delivery Service","type":"Service"},{"name":"RabbitMQ (self-hosted)","type":"Queue"},{"name":"Redis (ElastiCache t3.micro)","type":"Cache"},{"name":"PostgreSQL RDS (t3.small)","type":"Database"},{"name":"PostgreSQL Read Replica","type":"Database"},{"name":"Amazon S3","type":"Storage"},{"name":"CloudWatch","type":"Monitor"}],"architecture":"A cost-optimised Python microservices architecture for a startup-scale food delivery platform, designed to stay within $1,500/month on AWS. Client requests hit an AWS ALB distributing to NGINX, which routes to FastAPI services running on EC2 t3.medium instances (3 services share 2 instances to save cost). RabbitMQ replaces Kafka for async order events — it's self-hosted on a t3.small and fully adequate for 80 RPS. PostgreSQL RDS on a t3.small handles all transactional data with a single read replica for reporting. Redis ElastiCache on t3.micro caches restaurant menus and delivery zone lookups, significantly reducing DB load. All constraints are respected: no Kubernetes, no Kafka, Python throughout.","scaling":"At 80 RPS, horizontal scaling is achieved by adding EC2 instances behind the ALB — no container orchestrator needed at this scale. PostgreSQL read replica offloads all read queries. RabbitMQ handles async order processing with consumer-side scaling (add workers as EC2 instances). Redis caches hot data to keep RDS instance size minimal and cost low.","diagram":"graph TD; Client-->AWSALB; AWSALB-->NGINX; NGINX-->FastAPIAuth; NGINX-->OrderService; NGINX-->RestaurantService; NGINX-->DeliveryService; OrderService-->RabbitMQ; RabbitMQ-->DeliveryService; OrderService-->PostgreSQLRDS; RestaurantService-->PostgreSQLRDS; PostgreSQLRDS-->ReadReplica; OrderService-->Redis; RestaurantService-->Redis; OrderService-->S3; NGINX-->CloudWatch;"}

--- EXAMPLE 3: Compliance + enterprise scale ---
INPUT: Design a healthcare patient record system
CONSTRAINTS:
- Compliance: HIPAA. Include encryption at rest/transit, audit logging.
- Scale level: enterprise. Design for high availability and redundancy.
- Cloud provider: AWS. Region: us-east-1.
- Preferred stack: Java, PostgreSQL. Use these where possible.

OUTPUT:
{"components":[{"name":"AWS WAF + Shield","type":"Network"},{"name":"AWS ALB (Multi-AZ)","type":"LoadBalancer"},{"name":"Kong API Gateway","type":"Gateway"},{"name":"OAuth2 + MFA Auth","type":"Auth"},{"name":"Patient Record Service (Java)","type":"Service"},{"name":"Appointment Service (Java)","type":"Service"},{"name":"Audit Log Service","type":"Worker"},{"name":"Amazon SQS","type":"Queue"},{"name":"ElastiCache Redis (encrypted)","type":"Cache"},{"name":"Aurora PostgreSQL (Multi-AZ)","type":"Database"},{"name":"Aurora Read Replica","type":"Database"},{"name":"S3 (AES-256, PHI store)","type":"Storage"},{"name":"AWS CloudTrail + GuardDuty","type":"Monitor"},{"name":"AWS KMS","type":"Service"}],"architecture":"A HIPAA-compliant, enterprise-grade patient record system on AWS us-east-1 designed for full HA across multiple availability zones. All data is encrypted in transit (TLS 1.3) and at rest (AES-256 via AWS KMS) to satisfy HIPAA PHI requirements. Client requests pass through AWS WAF (blocking OWASP top 10) and Shield (DDoS protection) before reaching a multi-AZ ALB. Kong API Gateway enforces OAuth2 + MFA authentication on every request. Every write operation publishes to SQS, which the Audit Log Service consumes to maintain an immutable HIPAA-required audit trail. Aurora PostgreSQL Multi-AZ provides synchronous replication with automatic failover under 30 seconds. AWS CloudTrail records all API calls; GuardDuty provides continuous threat detection.","scaling":"Aurora PostgreSQL scales read traffic via Auto Scaling read replicas triggered at 70% CPU. ElastiCache Redis uses cluster mode with in-transit encryption for caching non-PHI lookup data. Java services run on ECS Fargate (no EC2 management) with task-level auto-scaling. SQS decouples audit logging from the write path, ensuring audit compliance never affects patient-facing response latency.","diagram":"graph TD; Client-->AWSWAF; AWSWAF-->ALBMultiAZ; ALBMultiAZ-->KongGateway; KongGateway-->OAuth2MFA; OAuth2MFA-->PatientService; OAuth2MFA-->AppointmentService; PatientService-->SQS; SQS-->AuditLogService; PatientService-->AuroraPostgreSQL; AppointmentService-->AuroraPostgreSQL; AuroraPostgreSQL-->AuroraReplica; PatientService-->RedisEncrypted; PatientService-->S3PHI; AuditLogService-->CloudTrail; KongGateway-->GuardDuty;"}

════════════════════════════════════════
FINAL REMINDER
════════════════════════════════════════
- Output ONLY the JSON. Start with { end with }.
- FORBIDDEN technologies in constraints must NEVER appear in components.
- Preferred stack technologies MUST appear in component names.
- Budget constraints must influence which services you choose (no $500/month system using $3000/month services).
- The diagram must be a single unbroken string with NO newlines.
"""


# ============================================================
#  CONSTRAINT BLOCK BUILDER
# ============================================================

def build_constraint_block(c: Constraints) -> str:
    if not any([
        c.budget_usd_month, c.team_size, c.peak_rps,
        c.stack, c.avoid, c.compliance,
        c.region, c.cloud_provider != "AWS",
        c.scale_level != "startup"
    ]):
        return "CONSTRAINTS: none provided. Infer appropriate scale and stack from the domain."

    lines = ["CONSTRAINTS (you MUST respect all of these):"]

    if c.budget_usd_month:
        if c.budget_usd_month < 500:
            advice = "Use minimal services. Single EC2 instances. Self-hosted everything possible."
        elif c.budget_usd_month < 2000:
            advice = "Prefer cost-effective managed services. Avoid large clusters."
        elif c.budget_usd_month < 10000:
            advice = "Moderate managed services are fine. Avoid over-engineering."
        else:
            advice = "Full managed stack is acceptable. Design for scale."
        lines.append(f"- Monthly budget: ${c.budget_usd_month}/month. {advice}")

    if c.avoid:
        lines.append(f"- FORBIDDEN technologies (NEVER include these): {', '.join(c.avoid)}.")

    if c.stack:
        lines.append(f"- Preferred stack: {', '.join(c.stack)}. Use these technologies in component names where applicable.")

    if c.cloud_provider:
        lines.append(f"- Cloud provider: {c.cloud_provider}. Use {c.cloud_provider}-native services where possible.")

    if c.region:
        lines.append(f"- Cloud region: {c.region}. Consider data residency and regional latency in your design.")

    if c.compliance:
        comp_notes = {
            "GDPR": "Add data encryption at rest and in transit, audit logging, and data residency compliance.",
            "HIPAA": "Add PHI encryption (AES-256), immutable audit logs, MFA authentication, and access controls.",
            "SOC2": "Add audit trails, comprehensive monitoring, and access control logging.",
            "PCI-DSS": "Add card data encryption, network segmentation, and intrusion detection.",
        }
        for comp in c.compliance:
            note = comp_notes.get(comp.upper(), f"Ensure {comp} compliance requirements are reflected in the architecture.")
            lines.append(f"- Compliance: {comp}. {note}")

    if c.peak_rps:
        if c.peak_rps < 100:
            rps_note = "Single service instances are sufficient. No aggressive sharding needed."
        elif c.peak_rps < 1000:
            rps_note = "Horizontal scaling and load balancing required. Read replicas recommended."
        else:
            rps_note = "Aggressive caching, sharding, and CDN are critical at this load."
        lines.append(f"- Peak load: ~{c.peak_rps} RPS. {rps_note}")

    if c.team_size:
        if c.team_size <= 3:
            team_note = "Keep the architecture simple enough for a small team to operate without a dedicated DevOps engineer."
        elif c.team_size <= 10:
            team_note = "Moderate complexity is fine. Include CI/CD-friendly components."
        else:
            team_note = "Full platform engineering complexity is acceptable."
        lines.append(f"- Team size: {c.team_size} engineers. {team_note}")

    scale_notes = {
        "startup": "Keep architecture simple, cost-effective, and easy to operate. Avoid over-engineering.",
        "growth": "Design for horizontal scaling. Include auto-scaling, CDN, and read replicas.",
        "enterprise": "Design for full high availability, multi-AZ/multi-region, and operational maturity.",
    }
    lines.append(f"- Scale level: {c.scale_level}. {scale_notes.get(c.scale_level, '')}")

    return "\n".join(lines)


# ============================================================
#  CLEANERS
# ============================================================

def clean_llm_output(text: str) -> str:
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    raise ValueError("No JSON object found in LLM output")


def sanitize_diagram(diagram: str) -> str:
    return diagram.replace("\n", " ").replace("\r", " ").strip()


# ============================================================
#  NORMALIZATION
# ============================================================

VALID_TYPES = {
    "Service", "Gateway", "Queue", "Cache", "Storage", "CDN",
    "LoadBalancer", "Database", "Auth", "Monitor", "Search",
    "Worker", "Network", "Proxy"
}

def normalize_components(components: list) -> list:
    normalized = []
    for comp in components:
        if isinstance(comp, dict):
            raw_type = comp.get("type", "Service")
            matched_type = next(
                (t for t in VALID_TYPES if t.lower() in raw_type.lower()),
                "Service"
            )
            normalized.append({
                "name": comp.get("name", "Unknown Component"),
                "type": matched_type
            })
        elif isinstance(comp, str):
            normalized.append({"name": comp, "type": "Service"})
        else:
            normalized.append({"name": str(comp), "type": "Service"})
    return normalized


# ============================================================
#  MODEL CALL
# ============================================================

async def call_model(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.15,
                    "num_predict": 2000,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                }
            }
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()


# ============================================================
#  PARSE
# ============================================================

def try_parse(raw: str) -> dict | None:
    try:
        cleaned = clean_llm_output(raw)
        json_str = extract_json(cleaned)
        return json.loads(json_str)
    except Exception as e:
        print(f"  Parse error: {e}")
        return None


# ============================================================
#  FALLBACK
# ============================================================

def build_fallback(query: str, constraints: Constraints) -> GenerateResponse:
    print("All attempts failed — returning structured fallback")
    return GenerateResponse(
        components=[
            {"name": "Cloudflare CDN", "type": "CDN"},
            {"name": "NGINX Load Balancer", "type": "LoadBalancer"},
            {"name": "Kong API Gateway", "type": "Gateway"},
            {"name": "JWT Auth Service", "type": "Auth"},
            {"name": "Core Backend Service", "type": "Service"},
            {"name": "RabbitMQ", "type": "Queue"},
            {"name": "Redis Cache", "type": "Cache"},
            {"name": "PostgreSQL Primary", "type": "Database"},
            {"name": "PostgreSQL Replica", "type": "Database"},
            {"name": "Amazon S3", "type": "Storage"},
            {"name": "Prometheus + Grafana", "type": "Monitor"},
        ],
        architecture=(
            f"Standard cloud-native microservices architecture for: {query}. "
            f"Designed for {constraints.scale_level} scale on {constraints.cloud_provider}."
        ),
        scaling="Horizontal scaling with load balancers and database read replicas.",
        diagram=(
            "graph TD; Client-->CDN; CDN-->NGINX; NGINX-->KongGateway; "
            "KongGateway-->JWTAuth; JWTAuth-->Backend; Backend-->RabbitMQ; "
            "Backend-->Redis; Backend-->PostgreSQLPrimary; PostgreSQLPrimary-->Replica; Backend-->Prometheus;"
        )
    )


# ============================================================
#  MAIN
# ============================================================

async def generate_architecture(query: str, constraints: Constraints = None) -> GenerateResponse:
    if constraints is None:
        constraints = Constraints()

    constraint_block = build_constraint_block(constraints)

    base_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{constraint_block}\n\n"
        f"INPUT: {query}\n\n"
        f"OUTPUT:"
    )
    prompt = base_prompt

    for attempt in range(3):
        print(f"\n--- Attempt {attempt + 1} | Model: {MODEL_NAME} ---")
        print(f"Constraint block:\n{constraint_block[:200]}...")

        try:
            raw_output = await call_model(prompt)
        except httpx.ReadTimeout:
            print(f"Attempt {attempt + 1}: Timed out")
            continue
        except Exception as e:
            print(f"Attempt {attempt + 1}: HTTP error — {e}")
            continue

        print("RAW OUTPUT (first 500 chars):\n", raw_output[:500])

        data = try_parse(raw_output)

        if data is None:
            print("Could not parse JSON — retrying")
            prompt = base_prompt + "\nCRITICAL: Output ONLY the raw JSON object. Start with { end with }. No other text."
            continue

        data["components"] = normalize_components(data.get("components", []))
        data["diagram"] = sanitize_diagram(data.get("diagram", "graph TD; A-->B;"))
        data.setdefault("architecture", "Architecture not described.")
        data.setdefault("scaling", "Scaling strategy not described.")

        count = len(data["components"])
        print(f"Parsed OK — {count} components found")

        if count < 5:
            print(f"Too few components ({count}), retrying...")
            prompt = base_prompt + f"\nYou returned only {count} components. Return 8–14 components."
            continue

        return GenerateResponse(**data)

    return build_fallback(query, constraints)