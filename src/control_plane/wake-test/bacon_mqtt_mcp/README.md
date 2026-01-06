# BACON MQTT MCP Server

Cross-machine Claude wake system using MQTT and MCP progress notifications.

## The Problem

Claude Code's native async background agents can only wake the main agent within the same process. There's no built-in mechanism for cross-machine wake notifications.

## The Solution

This MCP server provides a blocking `wait_for_message` tool that:
1. Subscribes to an MQTT topic
2. Sends progress notifications every 30s to keep the MCP connection alive
3. Returns when a message arrives (or timeout)
4. The sub-agent completion triggers Claude Code's native h2A wake mechanism

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Main Claude Code Session                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                         h2A Queue                                ││
│  │   [User Input] [Tool Results] [◄── SUB-AGENT WAKE ◄──]         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              ▲                                       │
│                              │ Native wake (sub-agent complete)      │
│  ┌───────────────────────────┴─────────────────────────────────────┐│
│  │              Background Sub-Agent ("mqtt-listener")              ││
│  │                                                                  ││
│  │   Calls: wait_for_message(topic="bacon/claude/zbook/inbox")     ││
│  │   BLOCKS until message arrives...                                ││
│  │   Returns message → Agent completes → Wake triggers!            ││
│  └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP tool call (blocking)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    bacon-mqtt-mcp Server                             │
│                                                                      │
│   wait_for_message() ──► MQTT subscribe ──► Progress every 30s     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         MQTT Broker
```

## Installation

```bash
# Clone or copy to your machine
cd bacon_mqtt_mcp

# Install with pip
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Configuration

### Claude Code Settings

Add to `~/.claude/settings.json`:

```json
{
  "env": {
    "MCP_TIMEOUT": "3600000",
    "MCP_TOOL_TIMEOUT": "3600000"
  },
  "mcpServers": {
    "bacon-mqtt": {
      "command": "python",
      "args": ["-m", "bacon_mqtt_mcp"],
      "timeout": 3600000,
      "env": {
        "MQTT_BROKER": "srv906866.hstgr.cloud",
        "MQTT_PORT": "1883"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | srv906866.hstgr.cloud | MQTT broker hostname |
| `MQTT_PORT` | 1883 | MQTT broker port |
| `MQTT_USERNAME` | (empty) | MQTT username if required |
| `MQTT_PASSWORD` | (empty) | MQTT password if required |

## Tools

### wait_for_message

Block until a message arrives on an MQTT topic.

```python
# Parameters
topic: str = None        # Full topic, or auto-constructed from session_id
session_id: str = None   # Used to construct topic: bacon/claude/{session_id}/inbox
timeout: int = 3600      # Max wait time in seconds

# Returns
{
    "status": "received" | "timeout" | "error",
    "message": <payload>,
    "topic": "bacon/claude/...",
    "elapsed_seconds": 45,
    "timestamp": "2026-01-06T..."
}
```

### send_message

Send a message to another Claude session.

```python
# Parameters
message: str             # Message content
target_session: str      # Target session ID (e.g., "zbook-main")
topic: str = None        # Override auto-constructed topic
message_type: str = "text"  # "text", "task", "wake", "response"

# Returns
{
    "status": "sent" | "error",
    "topic": "bacon/claude/...",
    "timestamp": "2026-01-06T..."
}
```

### check_messages

Quick non-blocking check for pending messages.

```python
# Parameters
topic: str = None
session_id: str = None
timeout: float = 0.5

# Returns
{
    "has_message": bool,
    "message": <payload or None>,
    "topic": "bacon/claude/..."
}
```

### get_status

Get server and connection status.

## Sub-Agent Setup

Create `.claude/agents/mqtt-listener.md`:

```markdown
---
name: mqtt-listener
description: Background MQTT listener for cross-machine messages
tools: mcp__bacon_mqtt__wait_for_message
model: haiku
---

You are a dedicated message listener. Your ONLY job:
1. Call wait_for_message(session_id="zbook-main") 
2. When a message arrives, return it to the main agent
3. Include the full message content

Do not attempt any other actions.
```

## Usage

### Start a Listener (ZBook)

```
> Spawn the mqtt-listener agent in the background to wait for messages
```

### Send a Message (EliteBook)

```
> Send a message to zbook-main: "Please run the test suite"
```

### Direct Testing

```bash
# Terminal 1: Start the MCP server directly for testing
python -m bacon_mqtt_mcp

# Terminal 2: Publish a test message
mosquitto_pub -h srv906866.hstgr.cloud -t "bacon/claude/test/inbox" -m '{"type":"test","content":"Hello!"}'
```

## How It Works

1. **Main agent spawns background sub-agent** with `run_in_background: true`
2. **Sub-agent calls `wait_for_message`** which blocks
3. **MCP server subscribes to MQTT** and waits
4. **Progress notifications every 30s** reset the MCP timeout
5. **Message arrives via MQTT** → MCP tool returns
6. **Sub-agent completes** → Native h2A wake triggers
7. **Main agent resumes** with the message

## Token Economics

- **During wait**: Zero tokens consumed (no inference running)
- **Sub-agent overhead**: ~13K tokens when spawned
- **Message relay**: Minimal tokens for response formatting

## Limitations

- Main Claude Code session must remain open (not terminated)
- Session timeout (~5 hours) still applies
- One listener per topic recommended
- MQTT QoS 1 (at least once) - may get duplicates

## License

MIT
