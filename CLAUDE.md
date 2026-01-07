# BACON-AI: Evolutionary Mesh

## Quick Reference

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
- **Product**: BACON-AI Evolutionary Mesh
- **Philosophy**: Self-Annealing, Distributed Intelligence, Human-In-The-Loop
- **Coding Style**: Asynchronous (aiomqtt), Type-hinted (SQLModel), Clean Docs

## Project Structure
```
src/
├── control_plane/    # FastAPI backend, MQTT handler
├── dashboard/        # React TypeScript frontend
└── agent_daemon/     # Agent listener daemon

documentation/
├── architecture/     # System design docs
├── functional/       # Feature specs
└── process/          # Workflow guides
```
