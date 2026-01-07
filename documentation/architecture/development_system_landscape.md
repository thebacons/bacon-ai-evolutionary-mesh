# Development System Landscape

This document describes the multi-environment development infrastructure for the BACON-AI Evolutionary Mesh.

## Architecture Overview

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

## Directory Structure

```
/opt/bacon-ai/
├── production/     # Port 8000 - main branch (LIVE)
├── integration/    # Port 8005 - merge testing
├── feature-physics/ # Port 8006
└── feature-gui/    # Port 8007
```

## Systemd Services

Each environment runs as an independent systemd service using a template:

```
/etc/systemd/system/bacon-env@.service
```

Service instances:
- `bacon-env@8000.service` → Production
- `bacon-env@8005.service` → Integration
- `bacon-env@8006.service` → Feature Physics
- `bacon-env@8007.service` → Feature GUI

## Deployment Workflow

### Deploy to Feature Branch
```bash
python deploy_hostinger.py --env feature-physics
```

### Promote Feature → Integration
```bash
python deploy_hostinger.py --env integration --from feature-physics
```

### Promote Integration → Production
```bash
python deploy_hostinger.py --env production --from integration
```

### Rollback Production
```bash
python deploy_hostinger.py --env production --rollback
```

## Available Environments

| Environment | Port | GitHub Branch | Purpose |
|-------------|------|---------------|---------|
| production | 8000 | main | Live system |
| integration | 8005 | - | Merge testing |
| feature-physics | 8006 | feature/* | Physics development |
| feature-gui | 8007 | feature/* | GUI development |

## Regression Testing Workflow

1. Develop and test on feature port (e.g., 8006)
2. Promote to integration (8005)
3. Run regression tests on 8005
4. If successful, promote to production (8000)
5. If issues found, rollback and fix on feature branch
