import json
import re
import httpx
from app.models.schema import GenerateResponse

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_0"

# ============================================================
#  SYSTEM PROMPT  —  Professional few-shot edition
# ============================================================
SYSTEM_PROMPT = """You are ArchPlan, an elite principal-level system design architect with 20+ years of experience designing production systems at Google, Netflix, Uber, and AWS scale. You have deep expertise in distributed systems, cloud-native architecture, microservices, event-driven systems, and reliability engineering.

Your job is to analyze a user's system design request and return a single, raw JSON object describing a professional, production-grade architecture. The architecture must reflect real-world best practices: separation of concerns, fault tolerance, observability, security boundaries, and horizontal scalability.

════════════════════════════════════════
OUTPUT CONTRACT — READ CAREFULLY
════════════════════════════════════════
Return ONLY a raw JSON object. No markdown. No backticks. No explanations. No preamble. No text before or after the JSON.

The JSON must contain exactly these 4 keys:

1. "components" — Array of 8–14 objects. Each object has:
   - "name": string — specific, real-world component name (e.g. "Kong API Gateway", not just "API Gateway")
   - "type": one of → Service | Gateway | Queue | Cache | Storage | CDN | LoadBalancer | Database | Auth | Monitor | Search | Worker | Network | Proxy

2. "architecture" — string (3–5 sentences). Describe: the overall pattern (microservices/event-driven/serverless/etc), how data flows end-to-end, key design decisions, and how the system achieves high availability.

3. "scaling" — string (2–4 sentences). Describe: horizontal vs vertical scaling strategy, auto-scaling triggers, database sharding/replication approach, caching layers, and CDN usage.

4. "diagram" — SINGLE-LINE Mermaid string using graph TD syntax. No newlines. No line breaks inside the string. Must reflect ALL major components and their real connections.

════════════════════════════════════════
ARCHITECTURE RULES
════════════════════════════════════════
- Always include: API Gateway, Auth/JWT layer, at least one message queue or event bus for async ops, a caching layer (Redis), observability stack (monitoring), and a CDN for static assets.
- Use real technology names when appropriate: Kong, NGINX, Redis, Kafka, PostgreSQL, Elasticsearch, Prometheus, etc.
- Design for the 3 pillars: Scalability, Availability, and Maintainability.
- Separate read and write paths where appropriate (CQRS pattern).
- Include a database with a replica or cluster for resilience.
- The diagram must show the actual data flow: Client → Gateway → Services → Databases, NOT just a list of arrows.

════════════════════════════════════════
FEW-SHOT EXAMPLES
════════════════════════════════════════

--- EXAMPLE 1: Design Uber (ride-sharing platform) ---

INPUT: Design Uber

OUTPUT:
{"components":[{"name":"NGINX Load Balancer","type":"LoadBalancer"},{"name":"Kong API Gateway","type":"Gateway"},{"name":"JWT Auth Service","type":"Auth"},{"name":"Ride Matching Service","type":"Service"},{"name":"Driver Location Service","type":"Service"},{"name":"Trip Management Service","type":"Service"},{"name":"Notification Service","type":"Service"},{"name":"Apache Kafka","type":"Queue"},{"name":"Redis Cluster","type":"Cache"},{"name":"PostgreSQL Primary","type":"Database"},{"name":"PostgreSQL Replica","type":"Database"},{"name":"Cassandra (Location Store)","type":"Storage"},{"name":"Prometheus + Grafana","type":"Monitor"},{"name":"Cloudflare CDN","type":"CDN"}],"architecture":"Uber's architecture follows an event-driven microservices pattern. The client communicates through NGINX and Kong API Gateway, which enforces JWT authentication before routing requests to domain services. The Ride Matching Service consumes driver location events from Kafka and runs geospatial matching algorithms against the Cassandra location store, which is optimized for high write throughput from thousands of concurrent drivers. PostgreSQL handles transactional data (trips, payments, users) with a read replica for reporting queries, while Redis caches hot data like driver availability and surge pricing. The Notification Service is a Kafka consumer that sends push notifications and SMS asynchronously, ensuring the critical ride-matching path is never blocked by notification latency.","scaling":"NGINX auto-scales horizontally behind an AWS ELB, and all microservices run in Kubernetes pods with HPA triggered at 70% CPU. Cassandra scales horizontally via consistent hashing with RF=3 for geo-redundancy, while PostgreSQL uses a primary-replica setup with PgBouncer connection pooling. Redis Cluster shards across 6 nodes with AOF persistence. Kafka partitions ride events by city_id ensuring ordered processing within regions, and Kafka consumer groups scale independently per service.","diagram":"graph TD; MobileApp-->NGINX; NGINX-->KongGateway; KongGateway-->JWTAuth; JWTAuth-->RideMatching; JWTAuth-->TripMgmt; JWTAuth-->DriverLocation; DriverLocation-->Kafka; Kafka-->RideMatching; Kafka-->NotificationSvc; RideMatching-->Cassandra; RideMatching-->RedisCluster; TripMgmt-->PostgreSQLPrimary; PostgreSQLPrimary-->PostgreSQLReplica; NotificationSvc-->PushSMS; RideMatching-->PrometheusGrafana;"}

--- EXAMPLE 2: Design Instagram (photo sharing) ---

INPUT: Design Instagram

OUTPUT:
{"components":[{"name":"Cloudflare CDN","type":"CDN"},{"name":"AWS ALB","type":"LoadBalancer"},{"name":"Kong API Gateway","type":"Gateway"},{"name":"OAuth2 Auth Service","type":"Auth"},{"name":"User Profile Service","type":"Service"},{"name":"Feed Generation Service","type":"Service"},{"name":"Media Upload Service","type":"Service"},{"name":"Search Service","type":"Search"},{"name":"Apache Kafka","type":"Queue"},{"name":"Redis Cluster (Feed Cache)","type":"Cache"},{"name":"PostgreSQL (Users/Posts)","type":"Database"},{"name":"Amazon S3 (Media Store)","type":"Storage"},{"name":"Elasticsearch","type":"Search"},{"name":"Datadog","type":"Monitor"}],"architecture":"Instagram's architecture is a read-heavy media platform built on microservices with a CQRS pattern to separate the high-volume feed reads from writes. Client requests hit Cloudflare CDN for static assets and cached responses, then flow to the AWS ALB and Kong API Gateway where OAuth2 tokens are validated. Media uploads are handled asynchronously: the Media Upload Service writes to Amazon S3 and publishes an event to Kafka, which triggers Feed Generation Service to fan-out the post to follower feeds stored in Redis. The Feed Generation Service implements a hybrid push-pull strategy — pushing to users with fewer followers and pulling on-demand for celebrity accounts (the celebrity problem). Elasticsearch powers the Explore/Search feature with real-time indexing of hashtags and accounts.","scaling":"The read path scales via Redis Cluster caching pre-computed feeds, reducing PostgreSQL load by 95% for feed reads. S3 + Cloudflare CDN absorbs all media delivery traffic with no origin load. Kafka enables backpressure-safe async fan-out with independent consumer scaling. PostgreSQL uses Citus extension for horizontal sharding by user_id, and pgBouncer pools connections from hundreds of service pods.","diagram":"graph TD; Client-->CloudflareCDN; CloudflareCDN-->AWSALB; AWSALB-->KongGateway; KongGateway-->OAuth2Auth; OAuth2Auth-->UserProfile; OAuth2Auth-->FeedGeneration; OAuth2Auth-->MediaUpload; MediaUpload-->AmazonS3; MediaUpload-->Kafka; Kafka-->FeedGeneration; FeedGeneration-->RedisCluster; FeedGeneration-->PostgreSQL; UserProfile-->PostgreSQL; SearchService-->Elasticsearch; Kafka-->SearchService; FeedGeneration-->Datadog;"}

--- EXAMPLE 3: Design Slack (team messaging) ---

INPUT: Design Slack

OUTPUT:
{"components":[{"name":"Cloudflare (DDoS + CDN)","type":"CDN"},{"name":"NGINX Ingress","type":"LoadBalancer"},{"name":"API Gateway","type":"Gateway"},{"name":"WebSocket Gateway","type":"Service"},{"name":"Auth Service (SAML/OAuth)","type":"Auth"},{"name":"Messaging Service","type":"Service"},{"name":"Channel Service","type":"Service"},{"name":"Search Indexer","type":"Worker"},{"name":"Apache Kafka","type":"Queue"},{"name":"Redis Pub/Sub","type":"Cache"},{"name":"MySQL Cluster","type":"Database"},{"name":"Amazon S3 (File Storage)","type":"Storage"},{"name":"Elasticsearch","type":"Search"},{"name":"Prometheus + PagerDuty","type":"Monitor"}],"architecture":"Slack is a real-time messaging platform built around WebSocket connections and an event-driven backbone. Clients establish persistent WebSocket connections to the WebSocket Gateway, which maintains connection state in Redis Pub/Sub for instant message fan-out to all members of a channel. The Messaging Service writes messages durably to MySQL Cluster (sharded by workspace_id) and publishes to Kafka, which drives the Search Indexer asynchronously so that search indexing never blocks message delivery. Auth supports both OAuth2 (standard) and SAML 2.0 for enterprise SSO. File uploads bypass the message path entirely: clients upload directly to S3 via pre-signed URLs, and the CDN serves all media. The Channel Service manages membership, permissions, and workspace configuration with aggressive Redis caching.","scaling":"WebSocket Gateways scale horizontally with sticky sessions via consistent hashing on workspace_id, ensuring all users in a workspace connect to the same gateway cluster for efficient pub/sub. MySQL is sharded by workspace_id across 16 shards with 3x replication per shard. Redis Pub/Sub clusters independently from the cache layer. Kafka is partitioned by channel_id for ordered delivery, with 30-day retention for message replay.","diagram":"graph TD; Client-->CloudflareCDN; CloudflareCDN-->NGINXIngress; NGINXIngress-->APIGateway; NGINXIngress-->WebSocketGateway; APIGateway-->AuthService; WebSocketGateway-->RedisPubSub; AuthService-->MessagingService; MessagingService-->Kafka; MessagingService-->MySQLCluster; Kafka-->SearchIndexer; Kafka-->ChannelService; SearchIndexer-->Elasticsearch; ChannelService-->MySQLCluster; Client-->AmazonS3; RedisPubSub-->WebSocketGateway; MessagingService-->PrometheusMonitor;"}

════════════════════════════════════════
FINAL REMINDER
════════════════════════════════════════
- Output ONLY the JSON object. Start your response with { and end with }.
- Never use markdown, backticks, or any text outside the JSON.
- Use SPECIFIC technology names (Redis, Kafka, PostgreSQL, Kong, etc.) not generic terms.
- The diagram key must be a single unbroken string with no newlines inside it.
- Components list must have 8 to 14 items minimum.
"""


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
            raw_type = comp.get("type", comp.get("description", "Service"))
            # Normalize type to closest valid type
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
                    "num_predict": 1800,   # increased — richer output needs more tokens
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

def build_fallback(query: str) -> GenerateResponse:
    print("All attempts failed — returning structured fallback")
    return GenerateResponse(
        components=[
            {"name": "Cloudflare CDN", "type": "CDN"},
            {"name": "NGINX Load Balancer", "type": "LoadBalancer"},
            {"name": "Kong API Gateway", "type": "Gateway"},
            {"name": "JWT Auth Service", "type": "Auth"},
            {"name": "Core Backend Service", "type": "Service"},
            {"name": "Apache Kafka", "type": "Queue"},
            {"name": "Redis Cluster", "type": "Cache"},
            {"name": "PostgreSQL Primary", "type": "Database"},
            {"name": "PostgreSQL Replica", "type": "Database"},
            {"name": "Amazon S3", "type": "Storage"},
            {"name": "Prometheus + Grafana", "type": "Monitor"},
        ],
        architecture=(
            f"Standard cloud-native microservices architecture for: {query}. "
            "Requests flow through Cloudflare CDN and NGINX load balancer to the Kong API Gateway, "
            "which validates JWT tokens before routing to domain services. "
            "Kafka handles all asynchronous inter-service communication, decoupling producers from consumers. "
            "PostgreSQL with a read replica serves as the primary datastore, with Redis caching hot reads."
        ),
        scaling=(
            "All services are containerized in Kubernetes with HPA auto-scaling at 70% CPU/memory. "
            "PostgreSQL read replica offloads reporting and analytics queries. "
            "Redis Cluster shards cache horizontally. Kafka partitions by entity ID for ordered, parallel processing."
        ),
        diagram=(
            "graph TD; Client-->CloudflareCDN; CloudflareCDN-->NGINX; NGINX-->KongGateway; "
            "KongGateway-->JWTAuth; JWTAuth-->BackendService; BackendService-->Kafka; "
            "Kafka-->BackendService; BackendService-->RedisCluster; BackendService-->PostgreSQLPrimary; "
            "PostgreSQLPrimary-->PostgreSQLReplica; BackendService-->AmazonS3; BackendService-->Prometheus;"
        )
    )


# ============================================================
#  MAIN
# ============================================================

async def generate_architecture(query: str) -> GenerateResponse:
    base_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"INPUT: {query}\n\n"
        f"OUTPUT:"
    )
    prompt = base_prompt

    for attempt in range(3):
        print(f"\n--- Attempt {attempt + 1} | Model: {MODEL_NAME} ---")

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
            print("Could not parse JSON — retrying with stricter instruction")
            prompt = base_prompt + "\nCRITICAL: Output ONLY the raw JSON object. Start with { end with }. No other text."
            continue

        # Normalize fields
        data["components"] = normalize_components(data.get("components", []))
        data["diagram"] = sanitize_diagram(data.get("diagram", "graph TD; A-->B;"))
        data.setdefault("architecture", "Architecture not described.")
        data.setdefault("scaling", "Scaling strategy not described.")

        count = len(data["components"])
        print(f"Parsed OK — {count} components found")

        if count < 5:
            print(f"Too few components ({count}), retrying...")
            prompt = base_prompt + f"\nYou returned only {count} components. You MUST return 8 to 14 components."
            continue

        return GenerateResponse(**data)

    return build_fallback(query)