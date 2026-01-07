# BACON-AI: MQTT Mesh - Gemini Configuration

> **OFFICIAL PROJECT NAME**: `bacon-ai-mqtt-mesh`
> **Do not invent new names!** This was decided on 2026-01-07.

## Project Overview

This is the BACON-AI MQTT Mesh project - a distributed multi-agent collaboration system using MQTT for real-time communication.

## Project Locations

| Environment | Path |
|------------|------|
| **Local (Windows)** | `C:\Users\colin\Claude-Work\Projects\bacon-ai-evolutionary-mesh\` |
| **Server (PoC)** | `/home/bacon/projects/bacon-ai-mqtt-mesh/` |
| **Server Production (future)** | `/opt/bacon-ai/...` |

## Key URLs

- **Production Dashboard**: http://srv906866.hstgr.cloud:8000/
- **Integration**: http://srv906866.hstgr.cloud:8005/
- **Feature Testing**: http://srv906866.hstgr.cloud:8006/
- **Benchmarking (shiftr)**: https://bacon-ai.cloud.shiftr.io/

## Available Workflows

- `/deploy` - Deploy to Hostinger environments
- `/github-pr` - GitHub PR workflow

## Branding Guidelines

- **Full Name**: BACON-AI MQTT Mesh
- **Short Name**: BACON-AI Mesh
- **Philosophy**: Self-Annealing, Distributed Intelligence, Human-In-The-Loop

## Development Priorities (as of 2026-01-07)

1. **Persistent Agent Daemon** - systemd services for auto-start
2. **Presence & Attention Model** - sleeping/active/idle states
3. **Agent Wake-Up System** - tmux send-keys mechanism
4. **Message Queue & Retry** - offline message handling
5. **Mem0 Integration** - semantic memory (API key in .env)
6. **MQTT Authentication** - DEFERRED (last priority for PoC)

## Related Projects

- `mqtt-collaboration-project` - Initial MQTT tests and wake-up lessons learned
- `documentation/benchmarking/SHIFTR_IO_BENCHMARK.md` - UI patterns and flow observations
- `documentation/benchmarking/proposals/NEXT_PHASE_UI_DESIGN_PROPOSAL.md` - Neural mesh aesthetic proposal
- `documentation/benchmarking/proposals/UI_BRAINSTORM_TEAM_DISCUSSION.md` - AI team UI study
