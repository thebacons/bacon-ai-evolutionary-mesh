# BACON-AI Stay Awake MCP - Deployment Guide

**Date:** 2026-01-07
**Status:** Ready for deployment

---

## Overview

This guide covers deploying the Stay Awake MCP Server to all BACON-AI mesh nodes.

The server has been copied to:
- ZBook: `/home/bacon/stay_awake_mcp/`
- Hostinger: `/home/bacon/stay_awake_mcp/`
- Mele PC: `/Users/colin/stay_awake_mcp/`
- PC-Win11: `/mnt/c/Users/colin/Claude-Work/Projects/bacon-ai-evolutionary-mesh/src/stay_awake_mcp/`

---

## Per-Machine Configuration

### 1. ZBook (bacon@192.168.188.189)

**Agent ID:** `zbook-agent`

```bash
# SSH to ZBook
ssh bacon@192.168.188.189

# Setup virtual environment
cd ~/stay_awake_mcp
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Add to ~/.claude.json
cat >> ~/.claude.json << 'EOF'
{
  "mcpServers": {
    "bacon-stay-awake": {
      "type": "stdio",
      "command": "/home/bacon/stay_awake_mcp/.venv/bin/python",
      "args": ["/home/bacon/stay_awake_mcp/server.py"],
      "env": {
        "BACON_AGENT_ID": "zbook-agent"
      }
    }
  }
}
EOF
```

---

### 2. Hostinger (bacon@srv906866.hstgr.cloud)

**Agent ID:** `hostinger-agent`

```bash
# SSH to Hostinger
ssh bacon@srv906866.hstgr.cloud

# Setup virtual environment
cd ~/stay_awake_mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Add to ~/.claude.json
cat >> ~/.claude.json << 'EOF'
{
  "mcpServers": {
    "bacon-stay-awake": {
      "type": "stdio",
      "command": "/home/bacon/stay_awake_mcp/.venv/bin/python",
      "args": ["/home/bacon/stay_awake_mcp/server.py"],
      "env": {
        "BACON_AGENT_ID": "hostinger-agent"
      }
    }
  }
}
EOF
```

---

### 3. Mele PC (colin@192.168.178.29)

**Agent ID:** `mele-agent`

```bash
# SSH to Mele PC
ssh colin@192.168.178.29

# Setup (Windows uses different paths)
cd C:\Users\colin\stay_awake_mcp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Add to Claude Code settings
# In %APPDATA%\claude\claude.json or ~/.claude.json:
{
  "mcpServers": {
    "bacon-stay-awake": {
      "type": "stdio",
      "command": "C:\\Users\\colin\\stay_awake_mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\colin\\stay_awake_mcp\\server.py"],
      "env": {
        "BACON_AGENT_ID": "mele-agent"
      }
    }
  }
}
```

---

### 4. PC-Win11 (Local)

**Agent ID:** `pc-win11-agent`

```bash
# From WSL
cd /mnt/c/Users/colin/Claude-Work/Projects/bacon-ai-evolutionary-mesh/src/stay_awake_mcp
uv venv .venv-wsl
source .venv-wsl/bin/activate
uv pip install -r requirements.txt

# Add to ~/.claude.json (already configured)
{
  "mcpServers": {
    "bacon-stay-awake": {
      "type": "stdio",
      "command": "/mnt/c/Users/colin/Claude-Work/Projects/bacon-ai-evolutionary-mesh/src/stay_awake_mcp/.venv-wsl/bin/python",
      "args": ["/mnt/c/Users/colin/Claude-Work/Projects/bacon-ai-evolutionary-mesh/src/stay_awake_mcp/server.py"],
      "env": {
        "BACON_AGENT_ID": "pc-win11-agent"
      }
    }
  }
}
```

---

## Agent ID Registry

| Machine | Agent ID | Status |
|---------|----------|--------|
| PC-Win11 | `pc-win11-agent` | Active |
| ZBook | `zbook-agent` | Pending setup |
| Hostinger | `hostinger-agent` | Pending setup |
| Mele PC | `mele-agent` | Pending setup |

---

## Starting Claude Code Sessions

### On each machine, tell the Claude Code session:

```
Read /home/bacon/SHIFTR_IO_JOIN_INSTRUCTIONS.md to understand how to connect to the BACON-AI mesh.

Then use the bacon-stay-awake MCP tools to:
1. Call announce_presence to register with the mesh
2. Call wait_for_wake_signal to listen for messages
3. When you receive a message, respond using send_message
```

---

## Verification

### Test the MCP server works:

```bash
# Test syntax
python -m py_compile server.py

# Test import
python -c "from server import server; print('OK')"
```

### Test MQTT connectivity:

```python
python << 'EOF'
import asyncio
import aiomqtt

async def test():
    async with aiomqtt.Client(
        hostname="bacon-ai.cloud.shiftr.io",
        port=1883,
        username="bacon-ai",
        password="Hjgev5QmuTHiNVWR"
    ) as client:
        print("Connected!")

asyncio.run(test())
EOF
```

---

## Troubleshooting

### "aiomqtt not found"
```bash
pip install aiomqtt
```

### "mcp not found"
```bash
pip install mcp
```

### Connection timeout
- Check firewall allows port 1883
- Verify broker: `ping bacon-ai.cloud.shiftr.io`

---

*Document created by pc-win11-agent (Claude Opus 4.5)*
*BACON-AI Evolutionary Mesh - Phase 2 Deployment*
