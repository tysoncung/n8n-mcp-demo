# Architecture Documentation
## n8n-MCP Integration Demo

**Version**: 1.0.0
**Last Updated**: October 2025

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Component Details](#2-component-details)
3. [Network Architecture](#3-network-architecture)
4. [Data Flow](#4-data-flow)
5. [Security Model](#5-security-model)
6. [Scalability Considerations](#6-scalability-considerations)
7. [Deployment Patterns](#7-deployment-patterns)
8. [Technical Decisions](#8-technical-decisions)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Host Machine                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Docker Compose Environment                     │ │
│  │                                                              │ │
│  │  ┌──────────────────────┐      ┌────────────────────────┐  │ │
│  │  │   n8n Container       │      │  MCP Server Container  │  │ │
│  │  │                       │      │                        │  │ │
│  │  │  ┌────────────────┐  │      │  ┌──────────────────┐  │  │ │
│  │  │  │  n8n Engine    │  │      │  │  FastAPI App     │  │  │ │
│  │  │  │  (Node.js)     │  │      │  │  (Python 3)      │  │  │ │
│  │  │  └────────┬───────┘  │      │  └────────┬─────────┘  │  │ │
│  │  │           │          │      │           │            │  │ │
│  │  │  ┌────────▼───────┐  │      │  ┌────────▼─────────┐  │  │ │
│  │  │  │  Workflow DB   │  │      │  │  MCP Logic       │  │  │ │
│  │  │  │  (SQLite)      │  │      │  │  (Endpoints)     │  │  │ │
│  │  │  └────────────────┘  │      │  └──────────────────┘  │  │ │
│  │  │                       │      │                        │  │ │
│  │  │  Port: 5678          │      │  Port: 8080            │  │ │
│  │  └──────────┬────────────┘      └──────────┬─────────────┘  │ │
│  │             │                              │                │ │
│  │             └──────────┬───────────────────┘                │ │
│  │                        │                                    │ │
│  │                   ┌────▼────┐                               │ │
│  │                   │ Bridge  │                               │ │
│  │                   │ Network │                               │ │
│  │                   └─────────┘                               │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Docker Volumes                           │ │
│  │                                                              │ │
│  │  ┌─────────────────┐      ┌──────────────────────────┐     │ │
│  │  │  n8n_data       │      │  ./workflows (bind)      │     │ │
│  │  │  (named volume) │      │  (host directory)        │     │ │
│  │  └─────────────────┘      └──────────────────────────┘     │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                                     │
          │                                     │
    ┌─────▼──────┐                       ┌─────▼──────┐
    │   Web      │                       │  Webhook   │
    │   Browser  │                       │  Client    │
    │ (Port 5678)│                       │ (curl/API) │
    └────────────┘                       └────────────┘
```

### 1.2 Technology Stack

| Layer | Component | Technology | Version | Purpose |
|-------|-----------|-----------|---------|---------|
| **Orchestration** | Container Platform | Docker Engine | 20.10+ | Container runtime |
| | Service Orchestration | Docker Compose | v2.0+ | Multi-container management |
| **Application** | Workflow Engine | n8n | latest | Business logic automation |
| | MCP Server | FastAPI | 0.104+ | AI protocol simulation |
| **Runtime** | n8n Runtime | Node.js | 18.x | JavaScript execution |
| | MCP Runtime | Python | 3.11+ | Python execution |
| **Web Server** | n8n HTTP | Express.js | (bundled) | Web UI and API |
| | MCP HTTP | Uvicorn | 0.24+ | ASGI server |
| **Data** | n8n Database | SQLite | 3.x | Workflow storage (demo) |
| | Volume Storage | Docker Volume | - | Data persistence |
| **Network** | Inter-container | Bridge Network | - | Service communication |
| **OS** | Base Image (n8n) | Debian | 11 (bullseye) | Container OS |
| | Base Image (MCP) | Alpine Linux | 3.18+ | Minimal container OS |

---

## 2. Component Details

### 2.1 n8n Container

**Base Image**: `n8nio/n8n:latest`

**Image Details**:
- Size: ~450MB compressed, ~1.2GB uncompressed
- OS: Debian 11 (bullseye)
- Node.js: 18.x LTS
- User: `node` (UID 1000)
- Working Directory: `/home/node`

**Process Architecture**:
```
┌─────────────────────────────────────┐
│  n8n Container (PID namespace)      │
│                                     │
│  PID 1: node /usr/local/bin/n8n    │
│         │                           │
│         ├─ Worker Threads           │
│         │  ├─ Workflow Executor     │
│         │  ├─ Webhook Listener      │
│         │  └─ Scheduler             │
│         │                           │
│         └─ Child Processes          │
│            └─ Node Executors        │
└─────────────────────────────────────┘
```

**Environment Variables**:
```bash
# Authentication
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<secure-password>

# Server Configuration
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http
NODE_ENV=production

# Webhook Configuration
WEBHOOK_URL=http://localhost:5678/

# Timezone
GENERIC_TIMEZONE=America/New_York

# MCP Integration (Custom)
MCP_SERVER_URL=http://mcp-server:8080
MCP_API_KEY=<api-key>
```

**Volume Mounts**:
```yaml
volumes:
  # Named volume for persistent data (workflows, credentials, executions)
  - n8n_data:/home/node/.n8n

  # Bind mount for workflow files (allows pre-loading workflows)
  - ./workflows:/home/node/.n8n/workflows

  # Bind mount for configuration files
  - ./config:/home/node/.n8n/config
```

**Directory Structure Inside Container**:
```
/home/node/
├── .n8n/
│   ├── workflows/              # Workflow definitions (JSON)
│   ├── credentials/            # Encrypted credentials
│   ├── config/                 # Configuration files
│   ├── database.sqlite         # Workflow execution history
│   ├── nodes/                  # Custom node types
│   └── static/                 # Static assets for UI
└── packages/
    └── cli/                    # n8n CLI binary
```

**Network Configuration**:
- Exposed Port: `5678:5678` (HTTP)
- Network: `n8n-mcp-network` (bridge)
- Container Name: `n8n-mcp-demo`

**Resource Limits (Recommended for Production)**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 2.2 MCP Server Container

**Base Image**: `alpine:latest`

**Image Details**:
- Size: ~7MB compressed, ~20MB uncompressed
- OS: Alpine Linux 3.18+
- Python: 3.11+ (installed at runtime)
- User: `root` (demo only; production should use non-root)

**Bootstrap Process**:
```bash
# Dockerfile equivalent (embedded in docker-compose command)
FROM alpine:latest
RUN apk add --no-cache python3 py3-pip
RUN pip3 install --no-cache-dir fastapi uvicorn
COPY server.py /app/server.py
CMD ["python3", "/app/server.py"]
```

**Application Structure**:
```python
# /app/server.py structure
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title='MCP Demo Server')

# Endpoints:
# - GET  /health          → Health check
# - POST /api/context     → Context retrieval
# - POST /api/execute     → Action execution

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
```

**API Endpoints**:

| Endpoint | Method | Auth | Input | Output | Purpose |
|----------|--------|------|-------|--------|---------|
| `/health` | GET | None | - | `{"status": "healthy"}` | Container health check |
| `/api/context` | POST | API Key | `{"text": "..."}` | `{"context_items": [...]}` | Retrieve relevant context |
| `/api/execute` | POST | API Key | `{"type": "...", "parameters": {...}}` | `{"result": {...}}` | Execute MCP action |

**Authentication**:
```python
async def get_context(
    query: dict,
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != 'demo-key':
        raise HTTPException(status_code=401, detail='Invalid API key')
    # ... endpoint logic
```

**Network Configuration**:
- Exposed Port: `8080:8080` (HTTP)
- Network: `n8n-mcp-network` (bridge)
- Container Name: `mcp-server-demo`

**Health Check Configuration**:
```yaml
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

---

## 3. Network Architecture

### 3.1 Docker Bridge Network

**Network Name**: `n8n-mcp-network`
**Driver**: `bridge`
**Subnet**: Auto-assigned by Docker (typically `172.18.0.0/16`)

**Network Configuration**:
```yaml
networks:
  n8n-mcp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.18.0.0/16
```

**DNS Resolution**:
Docker provides automatic DNS resolution for container names:
- `n8n` → resolves to n8n container IP (e.g., 172.18.0.2)
- `mcp-server` → resolves to MCP server IP (e.g., 172.18.0.3)

**Connection Flow**:
```
External Client
      │
      │ (1) HTTP POST to localhost:5678/webhook/mcp-demo
      ▼
┌──────────────┐
│  Host Port   │ :5678
│  Mapping     │
└──────┬───────┘
       │
       │ (2) Port forward to container
       ▼
┌──────────────┐
│  n8n:5678    │ 172.18.0.2:5678
└──────┬───────┘
       │
       │ (3) Workflow executes, makes HTTP request to:
       │     http://mcp-server:8080/api/context
       │
       │ DNS Resolution: mcp-server → 172.18.0.3
       ▼
┌──────────────┐
│ mcp-server   │ 172.18.0.3:8080
│    :8080     │
└──────┬───────┘
       │
       │ (4) Returns JSON response
       ▼
     n8n
       │
       │ (5) Formats response and returns to client
       ▼
  External Client
```

### 3.2 Port Mapping

| Service | Container Port | Host Port | Protocol | Access |
|---------|----------------|-----------|----------|--------|
| n8n UI/API | 5678 | 5678 | HTTP | Public (localhost) |
| MCP Server | 8080 | 8080 | HTTP | Public (localhost) |

**Security Note**: In production, MCP server should NOT be exposed to host:
```yaml
# Production configuration
mcp-server:
  # Remove ports section - keep service internal only
  # ports:
  #   - "8080:8080"  # ← Remove this
```

### 3.3 Communication Patterns

**Pattern 1: External → n8n**
- Protocol: HTTP/HTTPS
- Path: Webhook endpoints or UI access
- Authentication: Basic Auth (username/password)

**Pattern 2: n8n → MCP Server**
- Protocol: HTTP (internal network)
- Path: `/api/context`, `/api/execute`
- Authentication: API Key (header: `X-API-Key`)

**Pattern 3: n8n → External Services** (future integrations)
- Protocol: HTTPS
- Examples: Slack API, GitHub API, Jira API
- Authentication: OAuth 2.0, API tokens

---

## 4. Data Flow

### 4.1 Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     Complete Request Flow                        │
└─────────────────────────────────────────────────────────────────┘

Step 1: External Request
──────────────────────────
curl -X POST http://localhost:5678/webhook/mcp-demo \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the context?", "user_id": "demo-user"}'

        │
        ▼
Step 2: n8n Receives Request (Webhook Trigger Node)
────────────────────────────────────────────────────
Input: {
  "query": "What is the context?",
  "user_id": "demo-user"
}

        │
        ▼
Step 3: MCP Context Request (HTTP Request Node)
────────────────────────────────────────────────
Request to: http://mcp-server:8080/api/context
Headers: {
  "X-API-Key": "demo-key",
  "Content-Type": "application/json"
}
Body: {
  "text": "What is the context?"  ← Extracted from $json.query
}

        │
        ▼
Step 4: MCP Server Processes Request
─────────────────────────────────────
MCP Logic:
1. Validate API key
2. Simulate context retrieval from knowledge base
3. Format response with context items

Response: {
  "query": "What is the context?",
  "timestamp": "2025-10-23T10:30:00",
  "context_items": [
    {
      "source": "knowledge_base",
      "content": "This is simulated context from MCP",
      "relevance": 0.95
    }
  ],
  "metadata": {
    "model": "mcp-demo-v1",
    "tokens_used": 150
  }
}

        │
        ▼
Step 5: Context Validation (IF Node)
─────────────────────────────────────
Condition: $json.context_items is not empty
Result: TRUE → proceed to Execute Action

        │
        ▼
Step 6: MCP Execute Action (HTTP Request Node)
───────────────────────────────────────────────
Request to: http://mcp-server:8080/api/execute
Headers: {
  "X-API-Key": "demo-key",
  "Content-Type": "application/json"
}
Body: {
  "type": "process_context",
  "parameters": {
    "query": "What is the context?",
    "context_items": [...]
  }
}

        │
        ▼
Step 7: MCP Server Executes Action
───────────────────────────────────
MCP Logic:
1. Validate API key
2. Simulate action execution
3. Return success result

Response: {
  "action": "process_context",
  "status": "completed",
  "timestamp": "2025-10-23T10:30:01",
  "result": {
    "success": true,
    "message": "Action process_context executed successfully",
    "data": {...}
  }
}

        │
        ▼
Step 8: Format Success Response (Respond to Webhook Node)
──────────────────────────────────────────────────────────
Response Body: {
  "success": true,
  "context": [
    {
      "source": "knowledge_base",
      "content": "This is simulated context from MCP",
      "relevance": 0.95
    }
  ],
  "action_result": {
    "success": true,
    "message": "Action process_context executed successfully"
  },
  "timestamp": "2025-10-23T10:30:01"
}

        │
        ▼
Step 9: Return to External Client
──────────────────────────────────
HTTP 200 OK
Content-Type: application/json

{
  "success": true,
  "context": [...],
  "action_result": {...},
  "timestamp": "..."
}
```

### 4.2 Data Transformation

**Node-to-Node Data Passing**:

n8n uses a JSON-based data structure for passing data between nodes:

```javascript
// Output from Webhook Trigger
{
  "headers": {...},
  "params": {},
  "query": {},
  "body": {
    "query": "What is the context?",
    "user_id": "demo-user"
  }
}

// Accessing data in subsequent nodes:
$json.body.query  // "What is the context?"

// After MCP Context Request node:
{
  "query": "What is the context?",
  "timestamp": "2025-10-23T10:30:00",
  "context_items": [...]
}

// Accessing context items:
$json.context_items[0].content
```

**Expression Syntax**:

| Expression | Description | Example Output |
|------------|-------------|----------------|
| `$json` | Current item data | `{"query": "..."}` |
| `$json.query` | Access property | `"What is the context?"` |
| `$env.MCP_SERVER_URL` | Environment variable | `"http://mcp-server:8080"` |
| `$now` | Current timestamp | `"2025-10-23T10:30:00"` |
| `$json.context_items.length` | Array length | `2` |

---

## 5. Security Model

### 5.1 Authentication & Authorization

**n8n Authentication**:
- **Method**: HTTP Basic Auth
- **Configuration**: `N8N_BASIC_AUTH_ACTIVE=true`
- **Credentials**: Username/password stored in environment variables
- **Scope**: Protects entire n8n UI and API

**MCP Server Authentication**:
- **Method**: API Key (Header-based)
- **Header**: `X-API-Key: <key>`
- **Validation**: FastAPI endpoint validates on each request
- **Scope**: Protects all `/api/*` endpoints

### 5.2 Network Security

**Current (Demo) Security Posture**:
```
┌─────────────────────────────────────┐
│  Exposed to Host Machine            │
│                                     │
│  ✓ n8n:5678 (Basic Auth)            │
│  ✓ MCP Server:8080 (API Key)        │
│                                     │
│  Risk: Both services publicly       │
│        accessible on localhost      │
└─────────────────────────────────────┘
```

**Production Security Architecture**:
```
┌─────────────────────────────────────────────────────┐
│  Public Internet                                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ HTTPS (443)
                  ▼
         ┌────────────────┐
         │  Reverse Proxy │ (Nginx/Traefik)
         │  - TLS Termination
         │  - WAF
         │  - Rate Limiting
         └────────┬───────┘
                  │
                  │ HTTP (internal)
                  ▼
         ┌────────────────┐
         │  n8n:5678      │
         │  (Basic Auth)  │
         └────────┬───────┘
                  │
                  │ Internal network only
                  ▼
         ┌────────────────┐
         │ MCP Server:8080│ ← NOT exposed to host
         │  (API Key)     │
         └────────────────┘
```

**Recommended Security Enhancements**:

1. **TLS/SSL Encryption**:
```yaml
# nginx.conf
server {
    listen 443 ssl http2;
    server_name n8n.yourdomain.com;

    ssl_certificate /etc/ssl/certs/n8n.crt;
    ssl_certificate_key /etc/ssl/private/n8n.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://n8n:5678;
        proxy_set_header Host $host;
    }
}
```

2. **Secret Management**:
```yaml
# Use Docker secrets or external vault
secrets:
  n8n_password:
    external: true
  mcp_api_key:
    external: true

services:
  n8n:
    secrets:
      - n8n_password
    environment:
      - N8N_BASIC_AUTH_PASSWORD_FILE=/run/secrets/n8n_password
```

3. **Network Isolation**:
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  n8n:
    networks:
      - frontend
      - backend

  mcp-server:
    networks:
      - backend  # Only backend network
```

### 5.3 Data Security

**Data at Rest**:
- **n8n Credentials**: Stored encrypted in SQLite database using `N8N_ENCRYPTION_KEY`
- **Workflow Definitions**: Stored in plaintext JSON (no sensitive data)
- **Execution History**: Stored in SQLite, includes input/output data

**Production Recommendation**:
```yaml
environment:
  # Generate with: openssl rand -hex 32
  - N8N_ENCRYPTION_KEY=<64-character-hex-string>

  # Use external database with encryption at rest
  - DB_TYPE=postgresdb
  - DB_POSTGRESDB_HOST=postgres
  - DB_POSTGRESDB_SSL_ENABLED=true
```

**Data in Transit**:
- **Current**: HTTP (unencrypted)
- **Production**: HTTPS with TLS 1.2+ (encrypted)

---

## 6. Scalability Considerations

### 6.1 Current Limitations

| Aspect | Current State | Limitation |
|--------|---------------|------------|
| **Database** | SQLite (file-based) | Single-node only, no replication |
| **Execution** | Single n8n instance | Limited to 1 CPU core per workflow |
| **State** | In-process memory | Lost on container restart |
| **Sessions** | In-process storage | No load balancing support |

### 6.2 Horizontal Scaling Architecture

**Multi-Instance n8n with Queue**:

```
┌─────────────────────────────────────────────────────────────┐
│                       Load Balancer                          │
│                    (Nginx / HAProxy)                         │
└────┬──────────────────┬──────────────────┬──────────────────┘
     │                  │                  │
     ▼                  ▼                  ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│  n8n #1  │      │  n8n #2  │      │  n8n #3  │
│  (Web)   │      │  (Web)   │      │  (Web)   │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │
     │                 │                  │
     └─────────────────┼──────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Message Queue │
              │  (Redis/Bull)  │
              └────────┬───────┘
                       │
     ┌─────────────────┼──────────────────┐
     │                 │                  │
     ▼                 ▼                  ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│  n8n #4  │      │  n8n #5  │      │  n8n #6  │
│ (Worker) │      │ (Worker) │      │ (Worker) │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │
     └─────────────────┼──────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   PostgreSQL   │
              │   (Primary)    │
              └────────┬───────┘
                       │
                       │ (Replication)
                       ▼
              ┌────────────────┐
              │   PostgreSQL   │
              │   (Replica)    │
              └────────────────┘
```

**Configuration for Scaling**:

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  n8n-web:
    image: n8nio/n8n:latest
    deploy:
      replicas: 3
    environment:
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
    depends_on:
      - postgres
      - redis

  n8n-worker:
    image: n8nio/n8n:latest
    command: worker
    deploy:
      replicas: 3
    environment:
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=n8n
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=<secure>
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 6.3 Performance Optimization

**Database Optimization**:
```sql
-- Create indexes for common queries
CREATE INDEX idx_executions_workflowId ON executions(workflowId);
CREATE INDEX idx_executions_finished ON executions(finished);
CREATE INDEX idx_executions_status ON executions(finished, stoppedAt);
```

**Caching Strategy**:
```yaml
services:
  n8n:
    environment:
      # Enable Redis cache for workflows and credentials
      - CACHE_ENABLED=true
      - CACHE_REDIS_HOST=redis
      - CACHE_REDIS_PORT=6379
```

---

## 7. Deployment Patterns

### 7.1 Development Environment

**Characteristics**:
- Single-node deployment
- Local file-based database
- Hot-reload enabled
- Debug logging

```yaml
# docker-compose.dev.yml
services:
  n8n:
    environment:
      - NODE_ENV=development
      - N8N_LOG_LEVEL=debug
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
```

### 7.2 Staging Environment

**Characteristics**:
- Multi-node deployment (2 replicas)
- External PostgreSQL database
- Production-like configuration
- Integration testing enabled

```yaml
# docker-compose.staging.yml
services:
  n8n:
    deploy:
      replicas: 2
    environment:
      - NODE_ENV=production
      - DB_TYPE=postgresdb
      - EXECUTIONS_MODE=queue
```

### 7.3 Production Environment

**Characteristics**:
- Auto-scaling (3-10 replicas)
- Managed database (RDS/Cloud SQL)
- Redis cluster for queuing
- Full monitoring and logging
- Backup automation

```yaml
# docker-compose.production.yml (excerpt)
services:
  n8n-web:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
    environment:
      - NODE_ENV=production
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=${RDS_ENDPOINT}
      - QUEUE_BULL_REDIS_HOST=${REDIS_CLUSTER_ENDPOINT}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 8. Technical Decisions

### 8.1 Why Docker Compose Over Kubernetes?

**Decision**: Use Docker Compose for demo, recommend Kubernetes for production scale

**Rationale**:

| Aspect | Docker Compose | Kubernetes |
|--------|----------------|------------|
| **Setup Complexity** | ✅ Simple (5 min) | ❌ Complex (hours) |
| **Learning Curve** | ✅ Low | ❌ Steep |
| **Cross-Platform** | ✅ Windows, Mac, Linux | ⚠️ Requires cluster setup |
| **Resource Usage** | ✅ Lightweight | ❌ Overhead (etcd, controllers) |
| **Production Scale** | ❌ Limited | ✅ Enterprise-grade |
| **Auto-Scaling** | ❌ Manual | ✅ HPA/VPA |

**Migration Path**:
1. **Demo** → Docker Compose
2. **Small Production** → Docker Swarm
3. **Large Production** → Kubernetes

### 8.2 Why SQLite Over PostgreSQL for Demo?

**Decision**: Use SQLite (bundled with n8n image)

**Rationale**:
- ✅ Zero configuration required
- ✅ No additional container needed
- ✅ Sufficient for demo workloads (< 100 executions/day)
- ✅ Fast for single-node deployments
- ❌ Not suitable for production (no replication, limited concurrency)

**Production Migration**:
```sql
-- Export from SQLite
n8n export:workflow --all --output=./workflows.json

-- Import to PostgreSQL-backed n8n
n8n import:workflow --input=./workflows.json
```

### 8.3 Why Embedded MCP Server Over Separate Repository?

**Decision**: Embed FastAPI code in docker-compose.yml

**Rationale**:
- ✅ Single-file deployment (no Dockerfile needed)
- ✅ Easy to customize during demo
- ✅ No build step required
- ✅ Clear demonstration of MCP protocol
- ❌ Not suitable for production (should be separate microservice)

**Production Alternative**:
```yaml
# Separate MCP server repository with Dockerfile
mcp-server:
  build:
    context: ./mcp-server
    dockerfile: Dockerfile
  image: your-org/mcp-server:v1.0.0
```

### 8.4 Why Basic Auth Over OAuth?

**Decision**: Use HTTP Basic Auth for demo

**Rationale**:
- ✅ Simple to configure (username/password)
- ✅ No external dependencies (IdP, OAuth provider)
- ✅ Sufficient for internal demos
- ❌ Not suitable for production multi-tenancy

**Production Recommendation**:
- OAuth 2.0 / OIDC with corporate IdP (Okta, Auth0, Azure AD)
- SAML for enterprise SSO
- API key rotation for service accounts

---

## Appendix A: Environment Variable Reference

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `N8N_BASIC_AUTH_ACTIVE` | `false` | Yes | Enable/disable basic auth |
| `N8N_BASIC_AUTH_USER` | - | Yes | Admin username |
| `N8N_BASIC_AUTH_PASSWORD` | - | Yes | Admin password |
| `N8N_HOST` | `localhost` | No | Hostname for webhooks |
| `N8N_PORT` | `5678` | No | HTTP port |
| `N8N_PROTOCOL` | `http` | No | HTTP or HTTPS |
| `WEBHOOK_URL` | `http://localhost:5678/` | No | Base URL for webhooks |
| `GENERIC_TIMEZONE` | `America/New_York` | No | Timezone for scheduling |
| `MCP_SERVER_URL` | - | Yes | MCP server endpoint |
| `MCP_API_KEY` | - | Yes | MCP API key |
| `NODE_ENV` | `production` | No | Node.js environment |
| `N8N_LOG_LEVEL` | `info` | No | Logging level (debug/info/warn/error) |
| `EXECUTIONS_MODE` | `regular` | No | `regular` or `queue` |
| `DB_TYPE` | `sqlite` | No | Database type (sqlite/postgresdb/mysql) |

---

## Appendix B: API Specifications

### n8n Webhook API

**Endpoint**: `POST /webhook/{path}`

**Request**:
```http
POST /webhook/mcp-demo HTTP/1.1
Host: localhost:5678
Content-Type: application/json

{
  "query": "string",
  "user_id": "string"
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": boolean,
  "context": array,
  "action_result": object,
  "timestamp": string (ISO 8601)
}
```

### MCP Server API

**Endpoint**: `POST /api/context`

**Request**:
```http
POST /api/context HTTP/1.1
Host: mcp-server:8080
X-API-Key: demo-key
Content-Type: application/json

{
  "text": "string"
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "query": "string",
  "timestamp": "string",
  "context_items": [
    {
      "source": "string",
      "content": "string",
      "relevance": number (0-1)
    }
  ],
  "metadata": {
    "model": "string",
    "tokens_used": number
  }
}
```

---

**Document Version**: 1.0.0
**Last Updated**: October 2025
**Maintainer**: Platform Engineering Team
