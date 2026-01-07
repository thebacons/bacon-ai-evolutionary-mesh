# Development Process Guide

## Overview

This document outlines the development process for BACON-AI Evolutionary Mesh using the multi-environment DevOps workflow.

## 4-Tier Development Environment Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│ TIER 1: DEVELOPMENT (This PC)                                           │
│ ├── Local IDE (Antigravity/VS Code)                                     │
│ ├── Local testing with mock data                                        │
│ └── Git version control                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ TIER 2: TEST/STAGING (Hostinger - Ports 8006-8009)                       │
│ ├── 8006: FUT (Feature Under Test) - feature-physics                    │
│ ├── 8007: FUT-2 (Feature Under Test) - feature-gui                      │
│ ├── 8008: SIT-1 (System Integration Test) - no auth, dummy data         │
│ └── 8009: SIT-2 (System Integration Test) - with auth, real data        │
├─────────────────────────────────────────────────────────────────────────┤
│ TIER 3: INTEGRATION/REGRESSION (Hostinger - Port 8005)                   │
│ ├── Merged features testing                                              │
│ ├── Regression testing                                                   │
│ ├── Performance testing                                                  │
│ └── "Dress rehearsal" before production                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ TIER 4: PRODUCTION (Hostinger - Port 8000)                               │
│ └── Live system with real users                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| Tier | Environment | Location | Port | Purpose |
|------|-------------|----------|------|---------|
| 1 | Development | Local PC | N/A | IDE, coding, unit tests |
| 2 | FUT/SIT | Hostinger | 8006-8009 | Feature & integration testing |
| 3 | Regression | Hostinger | 8005 | Dress rehearsal, performance |
| 4 | Production | Hostinger | 8000 | Live system |

## Implementation Plan: Multi-Environment Development Infrastructure

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    HOSTINGER SERVER                          │
├─────────────────────────────────────────────────────────────┤
│  Port 8000 │ PRODUCTION    │ github/main branch             │
│  Port 8005 │ INTEGRATION   │ Merged features for regression │
│  Port 8006 │ FEATURE-A     │ Feature branch A testing       │
│  Port 8007 │ FEATURE-B     │ Feature branch B testing       │
└─────────────────────────────────────────────────────────────┘
```

### Server Directory Structure

```
/opt/bacon-ai/
├── production/     # Port 8000 - main branch
├── integration/    # Port 8005 - merge testing
├── feature-a/      # Port 8006
└── feature-b/      # Port 8007
```

### Phase 1: Environment Setup

**[NEW] `/etc/systemd/system/bacon-{env}.service`**

Environment-specific service files:

```ini
[Unit]
Description=BACON-AI Control Plane ({env})
After=network.target mosquitto.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bacon-ai/{env}
ExecStart=/opt/bacon-ai/{env}/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port {port}
Restart=always
RestartSec=5
Environment="BACON_ENV={env}"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

**[MODIFY] `deploy_hostinger.py`**

Add environment parameter:
- `--env production` → Port 8000
- `--env integration` → Port 8005
- `--env feature-physics` → Port 8006

### Phase 2: Workflow Commands

| Action | Command |
|--------|---------|
| Deploy to feature | `python deploy_hostinger.py --env feature-physics` |
| Test feature | Browse http://srv906866.hstgr.cloud:8006/ |
| Promote to integration | `python deploy_hostinger.py --env integration --from feature-physics` |
| Promote to production | `python deploy_hostinger.py --env production --from integration` |
| Rollback production | `python deploy_hostinger.py --env production --from integration` |

### Verification Plan

1. Deploy a test change to port 8006
2. Verify it works on 8006
3. Promote to 8005 and run regression
4. Promote to 8000 (production)

---

## Development Cycle

### 1. Feature Development

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Create feature branch (optional)                          │
│    └─ git checkout -b feature/my-feature                     │
│                                                               │
│ 2. Develop locally                                            │
│    └─ Edit code in src/                                       │
│                                                               │
│ 3. Deploy to feature port                                     │
│    └─ python deploy_hostinger.py --env feature-physics        │
│                                                               │
│ 4. Test at http://srv906866.hstgr.cloud:8006/                 │
└─────────────────────────────────────────────────────────────┘
```

### 2. Integration Testing

```
┌─────────────────────────────────────────────────────────────┐
│ 5. Promote to integration                                     │
│    └─ python deploy_hostinger.py --env integration --from feature-physics │
│                                                               │
│ 6. Run regression tests at http://srv906866.hstgr.cloud:8005/ │
└─────────────────────────────────────────────────────────────┘
```

### 3. Production Release

```
┌─────────────────────────────────────────────────────────────┐
│ 7. Create Pull Request (optional)                             │
│    └─ Use /github-pr workflow                                 │
│                                                               │
│ 8. Promote to production                                      │
│    └─ python deploy_hostinger.py --env production --from integration │
│                                                               │
│ 9. Verify at http://srv906866.hstgr.cloud:8000/               │
└─────────────────────────────────────────────────────────────┘
```

## Rollback Procedures

### Quick Rollback (from known-good environment)
```bash
python deploy_hostinger.py --env production --from integration
```

### Git-based Rollback
```bash
git checkout <previous-commit>
python deploy_hostinger.py --env production
```

## Agent Workflows

These workflows can be triggered by slash commands:

| Command | Description |
|---------|-------------|
| `/deploy` | Deploy to Hostinger environments |
| `/github-pr` | GitHub PR workflow for feature development |

## Related Documentation

- [Development System Landscape](../architecture/development_system_landscape.md) - Server architecture
- [Functional Specification](../functional/BACON_FUNCTIONAL_SPEC_V2.md) - Feature requirements
