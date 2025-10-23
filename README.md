# n8n-MCP Integration Demo

> A cross-platform demonstration of n8n workflow automation integrated with Model Context Protocol (MCP) using Docker containerization.

[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)
[![n8n](https://img.shields.io/badge/n8n-latest-orange.svg)](https://n8n.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 Overview

This repository contains a complete, production-ready demonstration of integrating n8n (workflow automation platform) with MCP (Model Context Protocol). The entire stack runs in Docker containers, ensuring consistent behavior across Windows and macOS environments.

### Key Features

- ✅ **Cross-platform compatibility** - Identical behavior on Windows and Mac
- ✅ **Containerized deployment** - Zero dependency installation required
- ✅ **Pre-configured workflow** - Ready-to-use n8n-MCP integration example
- ✅ **Simulated MCP server** - Demonstrates protocol integration patterns
- ✅ **Production-ready architecture** - Following infrastructure best practices
- ✅ **Comprehensive documentation** - Setup, troubleshooting, and architecture guides

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
│                                                             │
│  ┌──────────────┐                    ┌──────────────────┐   │
│  │              │                    │                  │   │
│  │   n8n        │◄──────HTTP────────►│   MCP Server     │   │
│  │   (Port 5678)│                    │   (Port 8080)    │   │
│  │              │                    │                  │   │
│  └──────┬───────┘                    └──────────────────┘   │
│         │                                                   │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          │ Webhook
          ▼
    External Client
   (curl, Postman, etc.)
```

### Components

1. **n8n Container**: Workflow automation engine with pre-loaded MCP integration workflow
2. **MCP Server Container**: FastAPI-based simulation of Model Context Protocol endpoints
3. **Docker Network**: Private network enabling secure inter-container communication
4. **Persistent Volume**: Stores n8n data, workflows, and configuration

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** 20.10+ ([Windows](https://docs.docker.com/desktop/install/windows-install/) | [Mac](https://docs.docker.com/desktop/install/mac-install/))
- **Git** for cloning the repository
- **8GB RAM** minimum (16GB recommended)
- **Ports available**: 5678 (n8n), 8080 (MCP server)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/n8n-mcp-demo.git
   cd n8n-mcp-demo
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env to customize credentials (optional)
   ```

3. **Start the stack**
   ```bash
   docker-compose up -d
   ```

4. **Verify services**
   ```bash
   docker-compose ps
   # Both containers should show "Up" status
   ```

5. **Access n8n and create owner account**
   - Open browser to http://localhost:5678
   - On first run, create an owner account with:
     - Email: your-email@example.com
     - First/Last name: Your Name
     - Password: (choose a secure password)
   - Login with your created credentials

## 📖 Usage

### Testing the MCP Integration

1. **Import the workflow**
   - In n8n UI, click "Workflows" in left sidebar
   - Click "+" or "Add Workflow"
   - Click "⋮" (three dots) menu → "Import from file"
   - Select `workflows/mcp-integration-demo.json` from the project directory
   - The workflow will open in the editor

2. **Activate the workflow**
   - Click "Activate" toggle in top right (should turn green/blue)
   - Workflow is now ready to receive webhook requests

3. **Test via Webhook**
   ```bash
   curl -X POST http://localhost:5678/webhook/mcp-demo \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is the current context?",
       "user_id": "demo-user"
     }'
   ```

3. **Expected Response**
   ```json
   {
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
     "timestamp": "2025-10-23T..."
   }
   ```

### Workflow Components

The demo workflow demonstrates:

1. **Webhook Trigger** - Receives HTTP POST requests
2. **MCP Context Request** - Fetches context from MCP server
3. **Context Validation** - Checks if valid context was returned
4. **Action Execution** - Processes context via MCP
5. **Response Formatting** - Returns structured JSON response

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `N8N_BASIC_AUTH_USER` | admin | n8n login username |
| `N8N_BASIC_AUTH_PASSWORD` | admin | n8n login password |
| `N8N_HOST` | localhost | n8n host address |
| `MCP_SERVER_URL` | http://mcp-server:8080 | MCP server endpoint |
| `MCP_API_KEY` | demo-key | API key for MCP authentication |
| `GENERIC_TIMEZONE` | America/New_York | Timezone for n8n |

### Customizing the MCP Server

The MCP server is a simple FastAPI application embedded in the docker-compose.yml. To customize:

1. Edit the Python code in `docker-compose.yml` under `mcp-server` service
2. Restart the containers: `docker-compose restart mcp-server`

Supported endpoints:
- `GET /health` - Health check
- `POST /api/context` - Retrieve context for a query
- `POST /api/execute` - Execute an action with parameters

## 🛠️ Troubleshooting

### Common Issues

**Containers won't start**
```bash
# Check port conflicts
docker-compose down
lsof -i :5678  # Mac
netstat -an | findstr 5678  # Windows

# Remove conflicting containers
docker-compose down -v
docker-compose up -d
```

**n8n shows "unauthorized"**
- Verify credentials in `.env` file
- Restart containers after changing `.env`:
  ```bash
  docker-compose restart
  ```

**MCP server connection fails**
```bash
# Check MCP server logs
docker logs mcp-server-demo

# Test MCP server directly
curl http://localhost:8080/health
```

**Workflow won't activate**
- Ensure both containers are running
- Check n8n logs: `docker logs n8n-mcp-demo`
- Verify MCP_SERVER_URL uses container name (`mcp-server`), not `localhost`

### Platform-Specific Notes

**Windows (WSL2)**
- Ensure WSL2 is enabled and Docker Desktop uses WSL2 backend
- File paths in docker-compose use Unix-style slashes
- Run commands in PowerShell or WSL2 terminal

**macOS**
- Docker Desktop must be running before `docker-compose up`
- For M1/M2 Macs, containers use ARM64 architecture (fully supported)

## 📊 Performance & Scaling

### Resource Usage

- **n8n container**: ~200MB RAM, <5% CPU (idle)
- **MCP server**: ~100MB RAM, <2% CPU (idle)
- **Total disk**: ~500MB (including Docker images)

### Scaling Recommendations

For production use:
1. Replace simulated MCP server with actual MCP implementation
2. Add reverse proxy (Nginx/Traefik) for HTTPS
3. Configure external database (PostgreSQL) for n8n
4. Implement proper secret management (HashiCorp Vault, AWS Secrets Manager)
5. Add monitoring (Prometheus + Grafana)

## 📁 Project Structure

```
n8n-mcp-demo/
├── .github/
│   └── workflows/         # CI/CD pipelines (optional)
├── config/                # n8n configuration files
├── docs/
│   ├── ARCHITECTURE.md    # Detailed architecture documentation
│   ├── PRESENTATION.md    # Technical presentation slides
│   └── TROUBLESHOOTING.md # Extended troubleshooting guide
├── workflows/
│   └── mcp-integration-demo.json  # Pre-configured workflow
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── docker-compose.yml    # Docker orchestration config
├── LICENSE               # MIT License
└── README.md            # This file
```

## 🔒 Security Considerations

- ⚠️ **Change default credentials** before production deployment
- ⚠️ **Use HTTPS** in production (not HTTP)
- ⚠️ **Rotate API keys** regularly
- ⚠️ **Network isolation** - MCP server not exposed to public internet
- ⚠️ **Volume permissions** - Ensure proper file ownership in Docker volumes

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [n8n](https://n8n.io/) - Workflow automation platform
- [FastAPI](https://fastapi.tiangolo.com/) - MCP server framework
- [Docker](https://www.docker.com/) - Containerization platform

## 📞 Support

- **Documentation**: See `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/n8n-mcp-demo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/n8n-mcp-demo/discussions)

---

**Built with** ❤️ **for Platform Engineers**
