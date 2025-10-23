# Troubleshooting Guide
## n8n-MCP Integration Demo

**Version**: 1.0.0
**Last Updated**: October 2025

---

## Table of Contents

1. [Pre-Deployment Checks](#1-pre-deployment-checks)
2. [Container Issues](#2-container-issues)
3. [Network Problems](#3-network-problems)
4. [Authentication Errors](#4-authentication-errors)
5. [Workflow Execution Failures](#5-workflow-execution-failures)
6. [Performance Issues](#6-performance-issues)
7. [Data Persistence Problems](#7-data-persistence-problems)
8. [Platform-Specific Issues](#8-platform-specific-issues)
9. [Diagnostic Commands](#9-diagnostic-commands)
10. [Getting Help](#10-getting-help)

---

## 1. Pre-Deployment Checks

### 1.1 Verify Docker Installation

**Issue**: Docker not installed or not running

**Symptoms**:
```bash
$ docker-compose up -d
-bash: docker-compose: command not found
```

**Solution**:

**macOS**:
```bash
# Check if Docker Desktop is running
open -a Docker

# Verify installation
docker --version
docker-compose --version

# If not installed, download from:
# https://docs.docker.com/desktop/install/mac-install/
```

**Windows (PowerShell)**:
```powershell
# Check Docker service status
Get-Service docker

# Verify installation
docker --version
docker-compose --version

# If not installed, download from:
# https://docs.docker.com/desktop/install/windows-install/
```

**Linux**:
```bash
# Check Docker service
sudo systemctl status docker

# Start if stopped
sudo systemctl start docker

# Install if missing (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 1.2 Check Port Availability

**Issue**: Required ports already in use

**Symptoms**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:5678: bind: address already in use
```

**Solution**:

**macOS/Linux**:
```bash
# Check what's using port 5678
lsof -i :5678

# Kill the process (replace PID)
kill -9 <PID>

# Check port 8080
lsof -i :8080
```

**Windows (PowerShell)**:
```powershell
# Check port 5678
netstat -ano | findstr :5678

# Kill process (replace PID)
taskkill /PID <PID> /F

# Check port 8080
netstat -ano | findstr :8080
```

**Alternative**: Change port mapping in `docker-compose.yml`:
```yaml
services:
  n8n:
    ports:
      - "15678:5678"  # Use port 15678 instead
```

### 1.3 Verify System Requirements

**Issue**: Insufficient resources

**Minimum Requirements**:
- **RAM**: 8GB (16GB recommended)
- **Disk**: 10GB free space
- **CPU**: 2 cores (4 cores recommended)

**Check Available Resources**:

**macOS**:
```bash
# Check memory
sysctl hw.memsize

# Check disk space
df -h /

# Check CPU cores
sysctl -n hw.ncpu
```

**Windows (PowerShell)**:
```powershell
# Check memory
Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum

# Check disk space
Get-PSDrive C

# Check CPU cores
$env:NUMBER_OF_PROCESSORS
```

**Linux**:
```bash
# Check memory
free -h

# Check disk space
df -h /

# Check CPU cores
nproc
```

---

## 2. Container Issues

### 2.1 Containers Won't Start

**Issue**: Containers fail to start or immediately exit

**Diagnostic Steps**:

```bash
# 1. Check container status
docker-compose ps

# Expected output:
# NAME              STATUS
# n8n-mcp-demo      Up X minutes
# mcp-server-demo   Up X minutes

# If status shows "Exit 1" or "Restarting":

# 2. View container logs
docker-compose logs n8n
docker-compose logs mcp-server

# 3. Check for specific errors (common patterns):
docker-compose logs | grep -i error
docker-compose logs | grep -i fail
```

**Common Causes & Solutions**:

#### 2.1.1 Missing Environment Variables

**Error**:
```
Error: Required environment variable MCP_SERVER_URL is not set
```

**Solution**:
```bash
# Verify .env file exists
ls -la .env

# If missing, create from template
cp .env.example .env

# Verify variables are loaded
docker-compose config | grep MCP_SERVER_URL
```

#### 2.1.2 Image Pull Failures

**Error**:
```
Error response from daemon: manifest for n8nio/n8n:latest not found
```

**Solution**:
```bash
# Pull images manually
docker pull n8nio/n8n:latest
docker pull alpine:latest

# If behind corporate proxy, configure Docker proxy:
mkdir -p ~/.docker
cat > ~/.docker/config.json <<EOF
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.corp.com:8080",
      "httpsProxy": "http://proxy.corp.com:8080"
    }
  }
}
EOF

# Restart Docker Desktop and retry
```

#### 2.1.3 Volume Permission Errors

**Error**:
```
Error: EACCES: permission denied, mkdir '/home/node/.n8n/workflows'
```

**Solution**:
```bash
# Linux/macOS: Fix permissions on bind-mounted directories
chmod -R 755 ./workflows
chmod -R 755 ./config

# If using SELinux (Linux), add :z flag to volumes:
# In docker-compose.yml:
volumes:
  - ./workflows:/home/node/.n8n/workflows:z
```

### 2.2 Containers Keep Restarting

**Issue**: Containers start but immediately restart in a loop

**Diagnostic**:
```bash
# Check restart count
docker inspect n8n-mcp-demo | grep RestartCount

# View last 50 log lines
docker logs --tail 50 n8n-mcp-demo

# Follow logs in real-time
docker logs -f n8n-mcp-demo
```

**Common Causes**:

#### 2.2.1 MCP Server Fails Health Check

**Error in logs**:
```
wget: can't connect to remote host (127.0.0.1): Connection refused
```

**Solution**:
```bash
# Check if MCP server is actually listening
docker exec mcp-server-demo netstat -tlnp | grep 8080

# If not listening, check Python errors:
docker logs mcp-server-demo 2>&1 | grep -A 10 "Traceback"

# Common issue: Missing Python dependencies
# Rebuild container:
docker-compose down
docker-compose up -d --force-recreate mcp-server
```

#### 2.2.2 n8n Database Corruption

**Error in logs**:
```
Error: SQLITE_CORRUPT: database disk image is malformed
```

**Solution**:
```bash
# Stop containers
docker-compose down

# Remove corrupted database
docker volume rm n8n-mcp-demo_n8n_data

# Restart (will create fresh database)
docker-compose up -d

# Note: This will delete all workflows and executions!
# For production, restore from backup instead.
```

### 2.3 Container Resource Limits

**Issue**: Containers killed due to OOM (Out of Memory)

**Error**:
```
Error: Container killed by OOM killer
```

**Diagnostic**:
```bash
# Check container memory usage
docker stats n8n-mcp-demo

# Example output showing high memory:
# CONTAINER      MEM USAGE / LIMIT     MEM %
# n8n-mcp-demo   1.8GiB / 2GiB        90.00%
```

**Solution**:
```yaml
# Add resource limits in docker-compose.yml
services:
  n8n:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

# Increase Docker Desktop memory allocation:
# Docker Desktop → Settings → Resources → Memory
# Set to at least 4GB (8GB recommended)
```

---

## 3. Network Problems

### 3.1 Cannot Access n8n UI

**Issue**: Browser shows "Unable to connect" at http://localhost:5678

**Diagnostic Steps**:

```bash
# 1. Verify container is running
docker-compose ps n8n

# 2. Check if port is accessible from host
curl -v http://localhost:5678

# 3. Check container logs for binding errors
docker logs n8n-mcp-demo | grep -i "listening\|bind"
```

**Solutions**:

#### 3.1.1 Port Not Forwarded

**Issue**: Container running but port not accessible

```bash
# Check port mapping
docker port n8n-mcp-demo

# Expected output:
# 5678/tcp -> 0.0.0.0:5678

# If missing, verify docker-compose.yml:
services:
  n8n:
    ports:
      - "5678:5678"  # Must be present

# Recreate container
docker-compose up -d --force-recreate n8n
```

#### 3.1.2 Firewall Blocking

**macOS**:
```bash
# Check if firewall is blocking
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Add Docker to allowed apps
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Docker.app
```

**Windows**:
```powershell
# Check Windows Defender Firewall
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Docker*"}

# Create inbound rule if missing
New-NetFirewallRule -DisplayName "Docker Desktop" -Direction Inbound -Protocol TCP -LocalPort 5678 -Action Allow
```

**Linux**:
```bash
# Check iptables/firewalld
sudo iptables -L -n | grep 5678

# Allow port if blocked
sudo iptables -A INPUT -p tcp --dport 5678 -j ACCEPT

# Or for firewalld:
sudo firewall-cmd --add-port=5678/tcp --permanent
sudo firewall-cmd --reload
```

### 3.2 n8n Cannot Reach MCP Server

**Issue**: Workflow fails with "Connection refused" to MCP server

**Error in n8n execution logs**:
```
Error: connect ECONNREFUSED 172.18.0.3:8080
```

**Diagnostic**:
```bash
# 1. Verify both containers are on same network
docker network inspect n8n-mcp-demo_n8n-mcp-network

# Should show both containers in "Containers" section:
# - n8n-mcp-demo
# - mcp-server-demo

# 2. Test connectivity from n8n container
docker exec n8n-mcp-demo wget -O- http://mcp-server:8080/health

# Expected: {"status": "healthy", "timestamp": "..."}
```

**Solutions**:

#### 3.2.1 Incorrect URL in Workflow

**Issue**: Using `localhost` instead of container name

**Wrong**:
```javascript
// In n8n HTTP Request node
url: "http://localhost:8080/api/context"  // ❌ Won't work
```

**Correct**:
```javascript
// In n8n HTTP Request node
url: "={{ $env.MCP_SERVER_URL }}/api/context"  // ✅ Correct

// Where MCP_SERVER_URL = http://mcp-server:8080
```

**Verification**:
```bash
# Check environment variable in container
docker exec n8n-mcp-demo env | grep MCP_SERVER_URL

# Should output:
# MCP_SERVER_URL=http://mcp-server:8080
```

#### 3.2.2 MCP Server Not Ready

**Issue**: n8n starts before MCP server is ready

**Solution**: Add startup delay or use health checks

```yaml
# docker-compose.yml
services:
  n8n:
    depends_on:
      mcp-server:
        condition: service_healthy  # Wait for health check

  mcp-server:
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s  # Give 30s for Python setup
```

### 3.3 Webhook Not Receiving Requests

**Issue**: External curl requests to webhook return 404

**Error**:
```bash
$ curl -X POST http://localhost:5678/webhook/mcp-demo
{"message":"Not Found"}
```

**Diagnostic**:
```bash
# 1. Verify workflow is active
# In n8n UI, check if toggle is green (Active)

# 2. Check webhook registration
docker logs n8n-mcp-demo | grep -i webhook

# Should see:
# Webhook "mcp-demo" registered successfully
```

**Solutions**:

#### 3.3.1 Workflow Not Activated

**Solution**:
1. Open n8n UI: http://localhost:5678
2. Navigate to "Workflows"
3. Click "MCP Integration Demo"
4. Click "Active" toggle (top right)
5. Wait for "Workflow activated" confirmation

#### 3.3.2 Incorrect Webhook Path

**Issue**: Workflow uses different path than curl command

**Verify**:
```json
// In workflows/mcp-integration-demo.json
{
  "parameters": {
    "path": "mcp-demo"  // ← Must match curl path
  }
}
```

**Test**:
```bash
# Ensure path matches workflow
curl -X POST http://localhost:5678/webhook/mcp-demo \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

---

## 4. Authentication Errors

### 4.1 Cannot Login to n8n

**Issue**: "Invalid credentials" when logging into n8n UI

**Symptoms**:
- Username/password not accepted
- HTTP 401 Unauthorized

**Diagnostic**:
```bash
# 1. Check configured credentials
cat .env | grep N8N_BASIC_AUTH

# 2. Verify environment variables in container
docker exec n8n-mcp-demo env | grep N8N_BASIC_AUTH_USER
docker exec n8n-mcp-demo env | grep N8N_BASIC_AUTH_PASSWORD
```

**Solutions**:

#### 4.1.1 Environment Variables Not Loaded

**Issue**: .env file not being read

```bash
# Verify docker-compose is reading .env
docker-compose config | grep N8N_BASIC_AUTH

# If variables show as empty or default values, restart containers:
docker-compose down
docker-compose up -d

# Wait 30 seconds for n8n to start
sleep 30

# Retry login
```

#### 4.1.2 Special Characters in Password

**Issue**: Password contains characters that require escaping

**Problem passwords**:
```bash
# ❌ Problematic characters: $, ", ', \, `
N8N_BASIC_AUTH_PASSWORD=pass$word123
N8N_BASIC_AUTH_PASSWORD=my"password
```

**Solution**:
```bash
# Use simple alphanumeric passwords for demo
N8N_BASIC_AUTH_PASSWORD=ChangeMeNow123

# Or properly escape in .env (single quotes)
N8N_BASIC_AUTH_PASSWORD='pass$word123'
```

### 4.2 MCP Server Returns 401 Unauthorized

**Issue**: n8n workflow fails at MCP Context Request node

**Error in workflow execution**:
```json
{
  "message": "Request failed with status code 401",
  "detail": "Invalid API key"
}
```

**Diagnostic**:
```bash
# 1. Check API key in environment
docker exec n8n-mcp-demo env | grep MCP_API_KEY

# 2. Test MCP server directly
curl -X POST http://localhost:8080/api/context \
  -H "X-API-Key: demo-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'

# Should return context, not 401
```

**Solutions**:

#### 4.2.1 API Key Mismatch

**Issue**: .env file has different key than MCP server expects

```bash
# Check MCP server code for expected key
docker exec mcp-server-demo cat /app/server.py | grep "if x_api_key"

# Output should show:
# if x_api_key != 'demo-key':

# Ensure .env matches:
echo "MCP_API_KEY=demo-key" >> .env

# Restart containers
docker-compose restart
```

#### 4.2.2 Header Not Sent by Workflow

**Issue**: HTTP Request node not configured correctly

**Verify in n8n workflow**:
```json
{
  "headerParameters": {
    "parameters": [
      {
        "name": "X-API-Key",
        "value": "={{ $env.MCP_API_KEY }}"  // ← Must be present
      }
    ]
  }
}
```

**If missing**: Re-import workflow from `workflows/mcp-integration-demo.json`

---

## 5. Workflow Execution Failures

### 5.1 Workflow Executes But Returns Error

**Issue**: Workflow activates successfully but returns error responses

**Diagnostic**:
```bash
# 1. Execute test request
curl -X POST http://localhost:5678/webhook/mcp-demo \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "user_id": "demo"}' \
  -v

# 2. Check execution in n8n UI
# Navigate to: Workflows → MCP Integration Demo → Executions

# 3. Click latest execution to see detailed node output
```

**Common Issues**:

#### 5.1.1 MCP Context Request Fails

**Error in execution**:
```json
{
  "success": false,
  "error": "No context found"
}
```

**Cause**: Context Check node determines context_items is empty

**Debug**:
1. In n8n UI, open execution
2. Click "MCP Context Request" node
3. Check "Output" tab for response from MCP server
4. Verify `context_items` array has elements

**Solution if empty**:
```bash
# Test MCP server directly
curl -X POST http://localhost:8080/api/context \
  -H "X-API-Key: demo-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "test query"}'

# Should return:
# {
#   "context_items": [...]  ← Must not be empty
# }

# If still empty, check MCP server logs:
docker logs mcp-server-demo
```

#### 5.1.2 JSON Parsing Errors

**Error**:
```
Error: Unexpected token } in JSON at position 123
```

**Cause**: Malformed JSON in request body or response formatting

**Solution**:
```bash
# Validate request JSON
echo '{"query": "test", "user_id": "demo"}' | jq .

# If jq fails, fix JSON syntax:
curl -X POST http://localhost:5678/webhook/mcp-demo \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "query": "What is the current context?",
  "user_id": "demo-user"
}
EOF
```

#### 5.1.3 Timeout Errors

**Error**:
```
Error: Timeout of 5000ms exceeded
```

**Solution**: Increase timeout in HTTP Request nodes

In n8n UI:
1. Open workflow
2. Click "MCP Context Request" node
3. Go to "Settings" tab
4. Increase "Timeout" from 5000ms to 30000ms (30 seconds)
5. Save workflow

### 5.2 Workflow Stops After First Node

**Issue**: Execution shows only Webhook Trigger executed, no subsequent nodes

**Cause**: Node connection broken or missing

**Solution**:
1. In n8n UI, open workflow editor
2. Verify connections between nodes (visual lines)
3. If missing, drag from output dot to input dot
4. Save workflow
5. Re-activate workflow

---

## 6. Performance Issues

### 6.1 Slow Workflow Execution

**Issue**: Workflow takes > 10 seconds to complete

**Diagnostic**:
```bash
# Measure execution time
time curl -X POST http://localhost:5678/webhook/mcp-demo \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Expected: < 2 seconds
# If > 5 seconds, investigate
```

**Solutions**:

#### 6.1.1 Container Resource Starvation

**Check resource usage**:
```bash
docker stats --no-stream n8n-mcp-demo mcp-server-demo

# Look for:
# - CPU % > 80%
# - MEM USAGE close to LIMIT
```

**Solution**:
```yaml
# Increase resource allocation in docker-compose.yml
services:
  n8n:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

# Or increase Docker Desktop allocation:
# Docker Desktop → Settings → Resources
# - CPUs: 4
# - Memory: 8GB
```

#### 6.1.2 Disk I/O Bottleneck

**Diagnostic**:
```bash
# Check Docker volume performance (macOS)
docker run --rm -v n8n-mcp-demo_n8n_data:/data alpine \
  sh -c "dd if=/dev/zero of=/data/test bs=1M count=100 && rm /data/test"

# Should see > 100 MB/s
# If < 50 MB/s, consider using named volumes instead of bind mounts
```

**Solution for macOS (VirtioFS)**:
```yaml
# In docker-compose.yml, ensure using named volumes
volumes:
  - n8n_data:/home/node/.n8n  # ✅ Fast (named volume)
  # NOT:
  # - ./data:/home/node/.n8n  # ❌ Slower (bind mount on Mac)
```

### 6.2 High Memory Usage

**Issue**: n8n container consuming > 1.5GB RAM

**Diagnostic**:
```bash
# Check detailed memory usage
docker exec n8n-mcp-demo ps aux --sort=-%mem | head -10
```

**Solutions**:

#### 6.2.1 Executions Not Being Pruned

**Issue**: Database storing too many old executions

**Solution**:
```bash
# Add execution retention settings
# In docker-compose.yml:
services:
  n8n:
    environment:
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - EXECUTIONS_DATA_MAX_AGE=168  # Keep only last 7 days
      - EXECUTIONS_DATA_PRUNE=true

# Restart to apply
docker-compose restart n8n
```

#### 6.2.2 Too Many Active Workflows

**Issue**: Multiple workflows polling external APIs

**Solution**: Deactivate unused workflows
1. n8n UI → Workflows
2. Click workflows you're not testing
3. Click "Active" toggle to deactivate

---

## 7. Data Persistence Problems

### 7.1 Workflows Disappear After Restart

**Issue**: Workflows not persisting across container restarts

**Diagnostic**:
```bash
# Check if workflows directory is bind-mounted
docker inspect n8n-mcp-demo | grep -A 5 "Mounts"

# Should show:
# "Source": "/Users/.../n8n-mcp-demo/workflows",
# "Destination": "/home/node/.n8n/workflows",
```

**Solution**:
```yaml
# Ensure bind mount in docker-compose.yml
services:
  n8n:
    volumes:
      - ./workflows:/home/node/.n8n/workflows  # ← Must be present
```

### 7.2 Cannot Import Workflow

**Issue**: "Import workflow" fails in n8n UI

**Error**:
```
Error: Invalid workflow format
```

**Solutions**:

#### 7.2.1 Validate JSON Format

```bash
# Validate workflow JSON
jq empty workflows/mcp-integration-demo.json

# If error, fix JSON syntax using jq:
jq . workflows/mcp-integration-demo.json > /tmp/fixed.json
mv /tmp/fixed.json workflows/mcp-integration-demo.json
```

#### 7.2.2 Manual Import via File Copy

```bash
# Copy workflow directly to container
docker cp workflows/mcp-integration-demo.json \
  n8n-mcp-demo:/home/node/.n8n/workflows/

# Restart n8n
docker-compose restart n8n

# Workflow should appear in UI after restart
```

---

## 8. Platform-Specific Issues

### 8.1 Windows (WSL2)

#### Issue: File Permissions Errors

**Error**:
```
Error: EPERM: operation not permitted
```

**Solution**:
```powershell
# Ensure project is in WSL filesystem, not /mnt/c
# Move project to WSL home directory:
wsl
cd ~
git clone https://github.com/yourusername/n8n-mcp-demo.git
cd n8n-mcp-demo
docker-compose up -d
```

#### Issue: Docker Desktop Not Using WSL2

**Verify**:
```powershell
wsl --list --verbose

# Should show Docker Desktop distribution using WSL2:
# NAME                   STATE           VERSION
# docker-desktop         Running         2
```

**Fix**:
1. Docker Desktop → Settings → General
2. Check "Use the WSL 2 based engine"
3. Restart Docker Desktop

### 8.2 macOS (M1/M2 Apple Silicon)

#### Issue: Platform Architecture Mismatch

**Error**:
```
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
```

**Solution**:
```yaml
# Specify platform in docker-compose.yml
services:
  n8n:
    platform: linux/amd64  # Or linux/arm64 for native

  mcp-server:
    platform: linux/arm64  # Alpine works on both
```

**Or use multi-arch images**:
```bash
# Pull both architectures
docker pull --platform linux/arm64 n8nio/n8n:latest
```

#### Issue: File Sharing Performance

**Symptom**: Very slow startup times

**Solution**:
```bash
# Use named volumes instead of bind mounts for data
# Only bind-mount read-only files

volumes:
  - n8n_data:/home/node/.n8n  # Named volume (fast)
  - ./workflows:/home/node/.n8n/workflows:ro  # Read-only bind
```

### 8.3 Linux

#### Issue: Permission Denied on Volumes

**Error**:
```
Error: EACCES: permission denied, open '/home/node/.n8n/database.sqlite'
```

**Solution**:
```bash
# Fix ownership (n8n runs as UID 1000)
sudo chown -R 1000:1000 ./workflows
sudo chown -R 1000:1000 ./config

# Or use SELinux context (if applicable)
chcon -Rt svirt_sandbox_file_t ./workflows
```

#### Issue: Docker Requires Sudo

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group change to take effect
# Or use newgrp:
newgrp docker

# Verify
docker ps  # Should work without sudo
```

---

## 9. Diagnostic Commands

### 9.1 Health Check Script

Save as `check-health.sh`:

```bash
#!/bin/bash

echo "=== n8n-MCP Demo Health Check ==="
echo

echo "[1/7] Checking Docker service..."
docker info > /dev/null 2>&1 && echo "✅ Docker running" || echo "❌ Docker not running"

echo
echo "[2/7] Checking container status..."
docker-compose ps

echo
echo "[3/7] Checking n8n health..."
curl -sf http://localhost:5678 > /dev/null && echo "✅ n8n accessible" || echo "❌ n8n not accessible"

echo
echo "[4/7] Checking MCP server health..."
curl -sf http://localhost:8080/health && echo "✅ MCP server healthy" || echo "❌ MCP server not responding"

echo
echo "[5/7] Checking network connectivity..."
docker exec n8n-mcp-demo wget -qO- http://mcp-server:8080/health > /dev/null 2>&1 && \
  echo "✅ n8n can reach MCP server" || echo "❌ Network connectivity issue"

echo
echo "[6/7] Checking resource usage..."
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" n8n-mcp-demo mcp-server-demo

echo
echo "[7/7] Checking recent errors in logs..."
echo "n8n errors:"
docker logs --since 5m n8n-mcp-demo 2>&1 | grep -i error | tail -3
echo "MCP server errors:"
docker logs --since 5m mcp-server-demo 2>&1 | grep -i error | tail -3

echo
echo "=== Health check complete ==="
```

Run with:
```bash
chmod +x check-health.sh
./check-health.sh
```

### 9.2 Log Collection Script

Save as `collect-logs.sh`:

```bash
#!/bin/bash

OUTPUT_DIR="debug-logs-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Collecting diagnostic information to $OUTPUT_DIR..."

# System info
docker version > "$OUTPUT_DIR/docker-version.txt" 2>&1
docker-compose version > "$OUTPUT_DIR/docker-compose-version.txt" 2>&1
uname -a > "$OUTPUT_DIR/system-info.txt" 2>&1

# Container status
docker-compose ps > "$OUTPUT_DIR/container-status.txt" 2>&1
docker-compose config > "$OUTPUT_DIR/docker-compose-resolved.yml" 2>&1

# Logs
docker logs n8n-mcp-demo > "$OUTPUT_DIR/n8n.log" 2>&1
docker logs mcp-server-demo > "$OUTPUT_DIR/mcp-server.log" 2>&1

# Configuration
cp .env "$OUTPUT_DIR/.env.txt" 2>/dev/null || echo ".env not found" > "$OUTPUT_DIR/.env.txt"
cp docker-compose.yml "$OUTPUT_DIR/" 2>/dev/null

# Network info
docker network inspect n8n-mcp-demo_n8n-mcp-network > "$OUTPUT_DIR/network-inspect.json" 2>&1

# Resource usage
docker stats --no-stream > "$OUTPUT_DIR/resource-usage.txt" 2>&1

echo "Logs collected in $OUTPUT_DIR/"
echo "You can share this directory when asking for help."
```

---

## 10. Getting Help

### 10.1 Before Asking for Help

**Please collect this information**:

1. **Run health check script** (see section 9.1)
2. **Collect logs** (see section 9.2)
3. **Note your environment**:
   - Operating system and version
   - Docker version (`docker --version`)
   - Docker Compose version (`docker-compose --version`)
   - Available RAM (`free -h` or `sysctl hw.memsize`)

### 10.2 Where to Get Help

**Project Resources**:
- **GitHub Issues**: https://github.com/yourusername/n8n-mcp-demo/issues
- **GitHub Discussions**: https://github.com/yourusername/n8n-mcp-demo/discussions

**Upstream Projects**:
- **n8n Forum**: https://community.n8n.io/
- **n8n Discord**: https://discord.gg/n8n
- **Docker Forum**: https://forums.docker.com/

**Stack Overflow** (use tags):
- `n8n`
- `docker-compose`
- `fastapi`

### 10.3 Creating a Good Bug Report

**Template**:

```markdown
## Environment
- OS: macOS 13.5 / Windows 11 / Ubuntu 22.04
- Docker: 24.0.6
- Docker Compose: v2.21.0

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Steps to Reproduce
1. Clone repository
2. Run `docker-compose up -d`
3. Execute: `curl -X POST ...`
4. Observe error

## Logs
```
[Paste relevant logs here]
```

## Screenshots
[If applicable]

## Additional Context
- Tried solution X from TROUBLESHOOTING.md
- Error started after changing Y
```

---

## Appendix: Common Error Messages

| Error Message | Section | Quick Fix |
|---------------|---------|-----------|
| `address already in use` | 1.2 | Kill process or change port |
| `permission denied` | 2.1.3, 8.3 | Fix file ownership: `chmod 755` |
| `ECONNREFUSED` | 3.2 | Check MCP_SERVER_URL uses container name |
| `Invalid credentials` | 4.1 | Verify .env and restart containers |
| `401 Unauthorized` | 4.2 | Check MCP_API_KEY matches |
| `Workflow not found` | 7.1 | Check volume mount for workflows |
| `database is locked` | 2.2.2 | Corrupted DB, remove volume |
| `Timeout exceeded` | 5.1.3 | Increase timeout in HTTP Request node |
| `No context found` | 5.1.1 | Check MCP server response has context_items |

---

**Document Version**: 1.0.0
**Last Updated**: October 2025
**Maintainer**: Platform Engineering Team

**Questions or suggestions?** Open an issue at:
https://github.com/yourusername/n8n-mcp-demo/issues
