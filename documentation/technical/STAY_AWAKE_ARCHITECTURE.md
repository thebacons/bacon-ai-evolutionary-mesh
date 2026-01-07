# Stay Awake Architecture - Technical Specification

| Field | Value |
|-------|-------|
| **Document ID** | TECH-SPEC-STAY-AWAKE-001 |
| **Version** | 1.0.0 |
| **Date** | 2026-01-07 |
| **Author** | pc-win11-agent (Claude Opus 4.5) |
| **Status** | Draft - For Team Review |
| **Project** | BACON-AI Evolutionary Mesh |

---

## 1. Executive Summary

This specification documents the **"Stay Awake" Architecture** - a pattern for keeping background Claude Code sub-agents alive indefinitely using MCP progress notifications. This enables persistent MQTT listeners that can wait for cross-machine wake signals without timing out.

### Key Innovation
MCP tools have a default timeout (typically 2 minutes). By sending periodic `ctx.report_progress()` calls, the timeout is reset, allowing blocking operations to run for hours.

---

## 2. Problem Statement

### 2.1 The Challenge
Claude Code sub-agents spawned via the `Task` tool with `run_in_background=true` will timeout after a period of inactivity. This prevents:
- Long-running MQTT listeners waiting for messages
- Persistent wake signal monitors
- Cross-machine coordination requiring extended waits

### 2.2 Previous Limitations
```
┌─────────────────────────────────────────────────────────┐
│  WITHOUT Stay Awake Pattern                             │
│                                                         │
│  Background Agent                                       │
│       │                                                 │
│       ▼                                                 │
│  Calls MCP Tool (e.g., wait_for_message)                │
│       │                                                 │
│       ▼                                                 │
│  [2 minutes pass with no response]                      │
│       │                                                 │
│       ▼                                                 │
│  ❌ TIMEOUT - Agent terminated                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Solution Architecture

### 3.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STAY AWAKE ARCHITECTURE                                                │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Main Claude Session                                            │    │
│  │                                                                 │    │
│  │  Task(                                                          │    │
│  │    subagent_type="general-purpose",                             │    │
│  │    run_in_background=True,                                      │    │
│  │    prompt="Call wait_for_message() for WAKE signals"            │    │
│  │  )                                                              │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                             │                                           │
│                             ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Background Sub-Agent                                           │    │
│  │                                                                 │    │
│  │  Calls: bacon-mqtt-mcp.wait_for_message(                        │    │
│  │           topic="bacon/v1/signal/pc-win11-agent",               │    │
│  │           timeout=3600                                          │    │
│  │         )                                                       │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                             │                                           │
│                             ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  bacon-mqtt-mcp MCP Server                                      │    │
│  │                                                                 │    │
│  │  ┌─────────────────────┐    ┌─────────────────────────────┐     │    │
│  │  │  mqtt_listener()    │    │  progress_reporter()        │     │    │
│  │  │                     │    │                             │     │    │
│  │  │  - Subscribes to    │    │  Every 30 seconds:          │     │    │
│  │  │    MQTT topic       │    │  ctx.report_progress(       │     │    │
│  │  │  - Blocks waiting   │    │    tick, max_ticks,         │     │    │
│  │  │    for message      │    │    "Listening... (Xs)"      │     │    │
│  │  │  - Sets event when  │    │  )                          │     │    │
│  │  │    message arrives  │    │                             │     │    │
│  │  └─────────────────────┘    │  This RESETS the timeout!   │     │    │
│  │           │                 └─────────────────────────────┘     │    │
│  │           │                              │                      │    │
│  │           └──────────────────────────────┘                      │    │
│  │                         │                                       │    │
│  │                         ▼                                       │    │
│  │              asyncio.Event() shared between both                │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  RESULT: Agent stays alive for up to 3600 seconds (1 hour)              │
│          waiting for an MQTT message!                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Sequence Diagram

```
Main Session          Background Agent         MCP Server              MQTT Broker
     │                      │                      │                       │
     │  Task(run_in_bg)     │                      │                       │
     │─────────────────────>│                      │                       │
     │                      │                      │                       │
     │                      │  wait_for_message()  │                       │
     │                      │─────────────────────>│                       │
     │                      │                      │                       │
     │                      │                      │  SUBSCRIBE topic      │
     │                      │                      │──────────────────────>│
     │                      │                      │                       │
     │                      │                      │  (waiting...)         │
     │                      │                      │                       │
     │                      │  progress(1/120)     │                       │
     │                      │<─────────────────────│  [30s elapsed]        │
     │                      │                      │                       │
     │                      │  progress(2/120)     │                       │
     │                      │<─────────────────────│  [60s elapsed]        │
     │                      │                      │                       │
     │                      │        ...           │       ...             │
     │                      │                      │                       │
     │                      │                      │  MESSAGE ARRIVES      │
     │                      │                      │<──────────────────────│
     │                      │                      │                       │
     │                      │  {status: "received"}│                       │
     │                      │<─────────────────────│                       │
     │                      │                      │                       │
     │  Agent completes     │                      │                       │
     │<─────────────────────│                      │                       │
     │                      │                      │                       │
     │  h2A Wake triggered  │                      │                       │
     │                      │                      │                       │
```

---

## 4. Implementation Details

### 4.1 Core MCP Server Code

**File:** `bacon_mqtt_mcp/server.py`

```python
async def progress_reporter(ctx):
    """Send progress notifications to keep connection alive."""
    tick = 0
    max_ticks = timeout // 30 + 1

    while not message_received.is_set():
        tick += 1
        elapsed = int(asyncio.get_event_loop().time() - start_time)

        # Report progress - this resets the MCP timeout!
        if ctx is not None:
            try:
                await ctx.report_progress(
                    tick,
                    max_ticks,
                    f"Listening on {subscribe_topic}... ({elapsed}s elapsed)"
                )
            except Exception as e:
                logger.warning(f"Progress report failed: {e}")

        logger.debug(f"Progress tick {tick}/{max_ticks}, elapsed: {elapsed}s")

        try:
            # Wait 30 seconds or until message received
            await asyncio.wait_for(
                message_received.wait(),
                timeout=30
            )
            return  # Message received, exit progress reporter
        except asyncio.TimeoutError:
            continue  # Keep sending progress
```

### 4.2 Key Components

| Component | Purpose | Interval |
|-----------|---------|----------|
| `mqtt_listener()` | Subscribes to MQTT topic, blocks until message | Continuous |
| `progress_reporter()` | Sends progress notifications | Every 30 seconds |
| `message_received` Event | Coordination between listener and reporter | Shared async Event |
| `ctx.report_progress()` | MCP framework call that resets timeout | Every 30 seconds |

### 4.3 The Magic: `ctx.report_progress()`

```python
await ctx.report_progress(
    tick,        # Current progress count
    max_ticks,   # Maximum expected ticks
    message      # Human-readable status
)
```

This MCP framework method:
1. Sends a progress notification to the calling agent
2. **Resets the MCP tool timeout counter**
3. Allows the tool to continue running indefinitely

---

## 5. Usage Patterns

### 5.1 Spawning a Persistent Listener

```python
# In main Claude session
Task(
    subagent_type="general-purpose",
    run_in_background=True,
    description="Persistent MQTT wake listener",
    prompt="""
    You are a persistent wake signal listener for the BACON-AI mesh.

    Call the bacon-mqtt-mcp wait_for_message tool with:
    - topic: bacon/v1/signal/pc-win11-agent
    - timeout: 3600

    When a message arrives:
    1. Parse the message content
    2. If it's a WAKE signal, report the wake reason
    3. If it's a TASK signal, describe the requested task

    Stay vigilant and report any received signals immediately.
    """
)
```

### 5.2 Sending a Wake Signal

```python
# From another machine/session
await send_message(
    message="Please process the pending analysis queue",
    topic="bacon/v1/signal/pc-win11-agent",
    message_type="wake"
)
```

### 5.3 Checking Listener Status

```python
# Use TaskOutput to check background agent status
TaskOutput(
    task_id="<background_agent_id>",
    block=False  # Non-blocking check
)
```

---

## 6. Configuration

### 6.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | srv906866.hstgr.cloud | MQTT broker hostname |
| `MQTT_PORT` | 1883 | MQTT broker port |
| `MQTT_USERNAME` | (empty) | Optional MQTT authentication |
| `MQTT_PASSWORD` | (empty) | Optional MQTT authentication |

### 6.2 Tunable Parameters

| Parameter | Default | Recommended Range | Notes |
|-----------|---------|-------------------|-------|
| `timeout` | 3600 (1 hour) | 300-86400 | Maximum wait time in seconds |
| Progress interval | 30 seconds | 15-60 | Hardcoded, requires code change |
| MQTT QoS | 1 | 0-2 | At-least-once delivery |

---

## 7. Integration with BACON-AI Mesh

### 7.1 Mesh Wake Signal Topics

| Topic Pattern | Purpose |
|---------------|---------|
| `bacon/v1/signal/{agent_id}` | Wake signal for specific agent |
| `bacon/v1/presence/agent/{agent_id}` | Heartbeat/presence announcements |
| `bacon/v1/broadcast/all` | Broadcast to all agents |

### 7.2 Wake Signal Payload Format

```json
{
  "type": "wake",
  "content": "Process pending analysis queue",
  "source": "mesh-orchestrator-main",
  "timestamp": "2026-01-07T15:30:00Z",
  "priority": "normal",
  "task_id": "TASK-001"
}
```

### 7.3 Recommended Mesh Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│  BACON-AI MESH - STAY AWAKE DEPLOYMENT                         │
│                                                                 │
│  Each node runs:                                                │
│  1. Main Claude session (interactive)                          │
│  2. Background wake listener (persistent)                       │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  zbook-agent    │  │  pc-win11-agent │  │  server-agent   │  │
│  │                 │  │                 │  │                 │  │
│  │  [Main]         │  │  [Main]         │  │  [Main]         │  │
│  │  [Wake Listener]│  │  [Wake Listener]│  │  [Wake Listener]│  │
│  │                 │  │                 │  │                 │  │
│  │  Listening on:  │  │  Listening on:  │  │  Listening on:  │  │
│  │  bacon/v1/      │  │  bacon/v1/      │  │  bacon/v1/      │  │
│  │  signal/zbook   │  │  signal/pc-win11│  │  signal/server  │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                │
│                                ▼                                │
│                    ┌───────────────────────┐                    │
│                    │  MQTT Broker          │                    │
│                    │  srv906866.hstgr.cloud│                    │
│                    │  :1883                │                    │
│                    └───────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Error Handling

### 8.1 Common Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| MQTT broker disconnect | `aiomqtt` exception | Auto-reconnect with backoff |
| Progress report failure | Exception in `report_progress()` | Log warning, continue |
| Timeout exceeded | `asyncio.TimeoutError` | Return `{status: "timeout"}` |
| Sub-agent crash | TaskOutput shows error | Respawn listener |

### 8.2 Resilience Recommendations

1. **Wrap in retry loop**: Main session should monitor and respawn failed listeners
2. **Heartbeat verification**: Periodically check listener is still running
3. **Graceful degradation**: If MQTT fails, fall back to polling

---

## 9. Testing

### 9.1 Unit Tests

```python
# test_stay_awake.py
async def test_progress_keeps_alive():
    """Verify progress notifications prevent timeout."""
    # Start wait_for_message with short timeout
    # Send progress notifications
    # Verify tool doesn't timeout prematurely

async def test_message_received():
    """Verify message reception terminates wait."""
    # Start wait_for_message
    # Publish MQTT message
    # Verify return with status="received"
```

### 9.2 Integration Tests

```bash
# 1. Start background listener
# 2. Wait 5 minutes (beyond normal timeout)
# 3. Send MQTT message
# 4. Verify listener received and responded
```

---

## 10. Security Considerations

| Concern | Mitigation |
|---------|------------|
| Unauthorized wake signals | Implement message signing/verification |
| MQTT topic hijacking | Use ACLs on MQTT broker |
| Resource exhaustion | Limit concurrent listeners per node |
| Message replay attacks | Include timestamp + nonce in messages |

---

## 11. Future Enhancements

1. **Dynamic progress interval**: Adjust based on network conditions
2. **Message acknowledgment**: Confirm wake signal received
3. **Priority queuing**: Handle high-priority wakes first
4. **Multi-topic listening**: Single listener for multiple signal types
5. **Encrypted payloads**: End-to-end encryption for sensitive commands

---

## 12. References

- **Source Implementation**: `bacon_mqtt_mcp/server.py`
- **MCP Specification**: [Model Context Protocol](https://modelcontextprotocol.io)
- **BACON-AI Protocol**: `documentation/architecture/BACON_SIGNAL_PROTOCOL_V1_2.md`
- **GitHub Issue**: User request for persistent agent listeners

---

## 13. Appendix: Full Source Code

### A.1 wait_for_message() Complete Implementation

See: `/mnt/c/Users/colin/Claude-Work/Projects/mqtt-collaboration-project/bacon_mqtt_mcp/server.py`

Lines 57-218 contain the complete implementation including:
- `wait_for_message()` tool definition
- `mqtt_listener()` async function
- `progress_reporter()` async function
- Error handling and cleanup

---

*Document generated by pc-win11-agent as part of BACON-AI mesh coordination.*
*For questions, contact the Lead Orchestrator (Gemini) or project maintainer.*
