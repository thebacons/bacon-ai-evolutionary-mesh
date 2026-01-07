---
description: GitHub PR workflow for feature development
---

# GitHub Pull Request Workflow

This workflow describes how to use GitHub PRs with the multi-environment deployment pipeline.

## 1. Create Feature Branch

```bash
# Using GitHub MCP tool:
# mcp_github-mcp-server_create_branch(owner="thebacons", repo="bacon-ai-evolutionary-mesh", branch="feature/my-feature")

# Or via git:
git checkout -b feature/my-feature
git push -u origin feature/my-feature
```

## 2. Develop and Test Locally

Make your changes in the local codebase.

## 3. Deploy to Feature Environment

```bash
// turbo
python deploy_hostinger.py --env feature-physics
```

Test at: http://srv906866.hstgr.cloud:8006/

## 4. Push Changes

```bash
git add .
git commit -m "Feature: description of changes"
git push origin feature/my-feature
```

## 5. Create Pull Request

```bash
# Using GitHub MCP tool:
# mcp_github-mcp-server_create_pull_request(
#   owner="thebacons",
#   repo="bacon-ai-evolutionary-mesh",
#   title="Feature: description",
#   head="feature/my-feature",
#   base="master"
# )
```

## 6. After PR Approved - Merge

```bash
# Using GitHub MCP tool:
# mcp_github-mcp-server_merge_pull_request(
#   owner="thebacons",
#   repo="bacon-ai-evolutionary-mesh",
#   pullNumber=<PR_NUMBER>
# )
```

## 7. Deploy to Production

```bash
// turbo
python deploy_hostinger.py --env production
```

## Quick Commands

| Action | Command |
|--------|---------|
| List PRs | `mcp_github-mcp-server_list_pull_requests` |
| Get PR details | `mcp_github-mcp-server_pull_request_read` |
| Request review | `mcp_github-mcp-server_update_pull_request` |
