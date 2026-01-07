# Development Process Guide

## Overview

This document outlines the development process for BACON-AI Evolutionary Mesh using the multi-environment DevOps workflow.

## Environment Matrix

| Environment | Port | Purpose | URL |
|-------------|------|---------|-----|
| Production | 8000 | Live system | http://srv906866.hstgr.cloud:8000/ |
| Integration | 8005 | Merge testing | http://srv906866.hstgr.cloud:8005/ |
| Feature | 8006+ | Feature testing | http://srv906866.hstgr.cloud:8006/ |

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

These workflows can be triggered by slash commands in Claude-Code or Antigravity IDE:

| Command | Description |
|---------|-------------|
| `/deploy` | Deploy to Hostinger environments |
| `/github-pr` | GitHub PR workflow for feature development |

## Related Documentation

- [Development System Landscape](architecture/development_system_landscape.md) - Server architecture
- [Functional Specification](functional/BACON_FUNCTIONAL_SPEC_V2.md) - Feature requirements
