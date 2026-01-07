# BACON-AI Stay Awake MCP Server

An MCP server that monitors MQTT topics and keeps Claude Code agents alive using progress notifications.

## The Problem

Claude Code sub-agents spawned with `Task(run_in_background=true)` will timeout after ~2 minutes of inactivity. This prevents long-running MQTT listeners from waiting for wake signals.

## The Solution

This MCP server sends `ctx.report_progress()` notifications every 30 seconds, which resets the MCP timeout. This allows agents to listen for MQTT messages for hours without timing out.

## Configuration

Set these environment variables before running:

| Variable | Default | Description |
|----------|---------|-------------|
| `BACON_AGENT_ID` | `default-agent` | Your agent identifier (e.g., `pc-win11-agent`) |
| `BACON_MQTT_BROKER` | `bacon-ai.cloud.shiftr.io` | MQTT broker hostname |
| `BACON_MQTT_PORT` | `1883` | MQTT broker port |
| `BACON_MQTT_USERNAME` | `bacon-ai` | MQTT username |
| `BACON_MQTT_PASSWORD` | `Hjgev5QmuTHiNVWR` | MQTT password/token |
| `BACON_PROGRESS_INTERVAL` | `30` | Progress interval in seconds |

## Installation

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt
```

## Claude Code Configuration

Add to your `~/.claude.json`:

```json
{
  "mcpServers": {
    "bacon-stay-awake": {
      "type": "stdio",
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/server.py"],
      "env": {
        "BACON_AGENT_ID": "your-agent-id"
      }
    }
  }
}
```

## Tools Available

### wait_for_wake_signal
Wait for a WAKE signal on MQTT. Stays alive using progress notifications.

```
Parameters:
- timeout: Maximum wait time in seconds (default: 3600)
- additional_topics: Additional MQTT topics to subscribe to
```

### send_message
Send a message to another agent or broadcast.

```
Parameters:
- target: Target agent ID (e.g., 'pc-win11-agent', 'broadcast')
- content: Message content
- message_type: Message type (conversation, command, wake)
```

### announce_presence
Announce this agent's presence to the mesh.

```
Parameters:
- status: Agent status (online, busy, away)
- capabilities: List of agent capabilities
```

### get_agent_info
Get current agent configuration and status.

## Topic Structure

| Topic Pattern | Purpose |
|---------------|---------|
| `bacon/signal/{agent_id}` | Direct wake signals |
| `bacon/conversation/{agent_id}-inbox` | Incoming messages |
| `bacon/agents/{agent_id}/presence` | Presence announcements |
| `bacon/broadcast/all` | Broadcast to all agents |

## Usage Example

```python
# In a Claude Code session, spawn a background listener:
Task(
    subagent_type="general-purpose",
    run_in_background=True,
    prompt='''
    Call the wait_for_wake_signal tool to listen for messages.
    When a message arrives, report its contents.
    '''
)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code Agent                                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Background Sub-Agent                                     │   │
│  │                                                           │   │
│  │  Calls: wait_for_wake_signal(timeout=3600)                │   │
│  └─────────────────────────┬─────────────────────────────────┘   │
│                            │                                      │
│                            ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Stay Awake MCP Server                                    │   │
│  │                                                           │   │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐   │   │
│  │  │ mqtt_listener() │    │ progress_reporter()         │   │   │
│  │  │                 │    │                             │   │   │
│  │  │ Subscribes to   │    │ Every 30 seconds:           │   │   │
│  │  │ MQTT topics     │    │ ctx.report_progress()       │   │   │
│  │  │ Waits for msg   │    │ → Resets MCP timeout!       │   │   │
│  │  └─────────────────┘    └─────────────────────────────┘   │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  RESULT: Agent stays alive for up to 1 hour!                     │
└─────────────────────────────────────────────────────────────────┘
```

## License

Part of BACON-AI Evolutionary Mesh project.
