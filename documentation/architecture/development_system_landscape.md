# Development System Landscape

Multi-environment development infrastructure for BACON-AI Evolutionary Mesh.

## Development Approach

**Local Development:**
- Single codebase at `c:\Users\colin\Claude-Work\Projects\bacon-ai-evolutionary-mesh\`
- No need for multiple local directories - **git handles version control**
- Deploy to test environments on Hostinger for validation

**Source of Truth:**
- **GitHub** is the source of truth for all code
- Local changes → push to GitHub → deploy to server

## Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HOSTINGER SERVER                          │
│                  srv906866.hstgr.cloud                       │
├─────────────────────────────────────────────────────────────┤
│  Port 8000 │ PRODUCTION    │ github/main branch             │
│  Port 8005 │ INTEGRATION   │ Merged features for regression │
│  Port 8006 │ FEATURE-A     │ Feature branch A testing       │
│  Port 8007 │ FEATURE-B     │ Feature branch B testing       │
└─────────────────────────────────────────────────────────────┘
```

## Server Directory Structure (only on Hostinger)

```
/opt/bacon-ai/
├── production/      # Port 8000
├── integration/     # Port 8005
├── feature-physics/ # Port 8006
└── feature-gui/     # Port 8007
```

## Deployment Commands

```bash
# Deploy local code to feature environment
python deploy_hostinger.py --env feature-physics

# Promote feature → integration
python deploy_hostinger.py --env integration --from feature-physics

# Promote integration → production
python deploy_hostinger.py --env production --from integration
```

## Rollback Strategy

| Method | Command | Use Case |
|--------|---------|----------|
| **From another env** | `--from integration` | Quick rollback from known-good env |
| **From GitHub** | `git checkout <commit> && redeploy` | Roll back to specific commit |

**Example: Production broke, rollback from integration:**
```bash
python deploy_hostinger.py --env production --from integration
```

**Example: Redeploy from GitHub:**
```bash
git checkout HEAD~1  # or specific commit hash
python deploy_hostinger.py --env production
```
