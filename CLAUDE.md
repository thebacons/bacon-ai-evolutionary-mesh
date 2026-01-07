# BACON-AI: MQTT Mesh

> **OFFICIAL PROJECT NAME**: `bacon-ai-mqtt-mesh`
> **Do not invent new names!** This was decided on 2026-01-07.

## Quick Reference

### Project Locations
| Location | Path |
|----------|------|
| **Local (Windows)** | `C:\Users\colin\Claude-Work\Projects\bacon-ai-evolutionary-mesh\` |
| **Server (PoC)** | `/home/bacon/projects/bacon-ai-mqtt-mesh/` |
| **Server (Production)** | `/opt/bacon-ai/...` (future) |

### Development Commands
```bash
# Run Control Plane locally
python src/control_plane/main.py

# Deploy to feature environment
python deploy_hostinger.py --env feature-physics

# Promote to production
python deploy_hostinger.py --env production --from integration

# Run Tests
pytest src/tests/
```

### Workflows
Use these slash commands for automated workflows:
- `/deploy` - Deploy to Hostinger environments
- `/github-pr` - GitHub PR workflow for feature development

### Multi-Environment URLs
| Environment | URL |
|-------------|-----|
| Production | http://srv906866.hstgr.cloud:8000/ |
| Integration | http://srv906866.hstgr.cloud:8005/ |
| Feature-Physics | http://srv906866.hstgr.cloud:8006/ |

### GitHub Repository
- **Owner**: thebacons
- **Repo**: bacon-ai-evolutionary-mesh
- **Default Branch**: master

### Key Documentation
- [Development System Landscape](documentation/architecture/development_system_landscape.md) - DevOps workflow
- [Functional Spec](documentation/functional/BACON_FUNCTIONAL_SPEC_V2.md) - Feature requirements

## Branding & Philosophy
- **Product**: BACON-AI MQTT Mesh
- **Philosophy**: Self-Annealing, Distributed Intelligence, Human-In-The-Loop
- **Coding Style**: Asynchronous (aiomqtt), Type-hinted (SQLModel), Clean Docs

## Key Features
- **Control Plane**: FastAPI server with MQTT monitoring
- **Dashboard**: React TypeScript force-graph visualization
- **Memory Service**: Mem0 Cloud for semantic memory (API key in .env)
- **Presence Model**: Agent sleeping/active/idle states

## Project Structure
```
src/
├── control_plane/    # FastAPI backend, MQTT handler, Mem0 gateway
├── dashboard/        # React TypeScript frontend
└── agent_daemon/     # Agent listener daemon

documentation/
├── architecture/     # System design docs
├── functional/       # Feature specs
└── process/          # Workflow guides
```
