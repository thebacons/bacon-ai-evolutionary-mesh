---
description: Deploy to multi-environment Hostinger infrastructure
---

# Deployment Workflow

## Environments

| Environment | Port | Service |
|-------------|------|---------|
| production | 8000 | bacon-production.service |
| integration | 8005 | bacon-integration.service |
| feature-physics | 8006 | bacon-feature-physics.service |
| feature-gui | 8007 | bacon-feature-gui.service |

## Deploy to Feature Environment

```bash
// turbo
python deploy_hostinger.py --env feature-physics
```

Test at: http://srv906866.hstgr.cloud:8006/

## Promote Feature to Integration

```bash
// turbo
python deploy_hostinger.py --env integration --from feature-physics
```

Test at: http://srv906866.hstgr.cloud:8005/

## Promote to Production

```bash
python deploy_hostinger.py --env production --from integration
```

Live at: http://srv906866.hstgr.cloud:8000/

## Rollback Production

If production is broken, restore from integration:

```bash
python deploy_hostinger.py --env production --from integration
```

## List Available Environments

```bash
// turbo
python deploy_hostinger.py --list
```
