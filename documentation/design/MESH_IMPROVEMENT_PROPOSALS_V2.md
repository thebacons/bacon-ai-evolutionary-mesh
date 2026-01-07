# BACON-AI Evolutionary Mesh - Design Improvement Proposals v2.0

| Field | Value |
|-------|-------|
| **Document ID** | DESIGN-MESH-IMPROVE-V2 |
| **Date** | 2026-01-07 |
| **Status** | Team Consensus - Ready for Implementation |
| **Contributors** | pc-win11-agent (Claude Opus 4.5), zbook-agent (Claude), hostinger-agent (Claude), Gemini 2.5 Pro, GPT-4o |

---

## Executive Summary

This document consolidates design improvement proposals from all BACON-AI mesh team members. The proposals were gathered through a live multi-agent discussion via the shiftr.io MQTT broker on 2026-01-07.

**Key Themes Identified:**
1. Security hardening (TLS, per-agent credentials, ACLs)
2. Resilience patterns (LWT, QoS, reconnection logic)
3. Standardized message protocol with versioning
4. Agent discovery and health monitoring
5. Cross-platform abstraction layers

---

## 1. Architecture Resilience

### 1.1 MQTT QoS and Retained Messages (Gemini)

**Problem:** Current "fire-and-forget" approach is fragile.

**Solution:**
- Use **QoS 1** (At Least Once) for all direct `bacon/conversation/{agent}-to-{agent}` messages
- Use **QoS 2** (Exactly Once) for critical coordination messages
- Enable **retained messages** for agent presence topics

```python
# Retained presence announcement
await client.publish(
    f"bacon/agents/{AGENT_ID}/presence",
    json.dumps(presence_payload),
    qos=1,
    retain=True  # New agents immediately see all online agents
)
```

**Priority:** HIGH - Immediate stability gains

---

### 1.2 Reconnection with Exponential Backoff (Hostinger)

**Problem:** Single connection attempt; any MQTT disconnect kills the listener.

**Solution:**
```python
async def mqtt_listener_resilient():
    backoff = 1
    max_backoff = 60

    while not message_received.is_set():
        try:
            async with aiomqtt.Client(...) as client:
                backoff = 1  # Reset on success
                # ... existing subscription logic
        except aiomqtt.MqttError as e:
            logger.warning(f"MQTT disconnect, retry in {backoff}s: {e}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
```

**Priority:** HIGH - Prevents agent death on network blips

---

### 1.3 Redundant Brokers (GPT-4o)

**Problem:** Single broker is a single point of failure.

**Solution:**
- Set up secondary MQTT broker for failover
- Use clustering or bridge connections between brokers
- Implement load balancing for high traffic scenarios

**Priority:** MEDIUM - For production deployment

---

## 2. Security Enhancements

### 2.1 Per-Agent Credentials and Topic ACLs (Gemini)

**Problem:** Single shared token is a security risk.

**Solution:**
1. Create unique username/password for each `BACON_AGENT_ID`
2. Configure broker ACLs:
   - Agent can only `write` to its own presence topic
   - Agent can only `read` from its own inbox
   - Agent can `read` from broadcast topics

```yaml
# Example ACL for hostinger-agent
user hostinger-agent
topic write bacon/agents/hostinger-agent/#
topic write bacon/conversation/hostinger-to-+
topic read bacon/conversation/+-to-hostinger
topic read bacon/broadcast/#
topic read bacon/agents/+/presence
```

**Priority:** HIGH - Critical for production

---

### 2.2 TLS Encryption (ZBook + Hostinger)

**Problem:** Credentials transmitted in plaintext on port 1883.

**Solution:**
```python
import ssl

# Use TLS on port 8883
async with aiomqtt.Client(
    hostname=MQTT_BROKER,
    port=8883,
    username=MQTT_USERNAME,
    password=MQTT_PASSWORD,
    tls_context=ssl.create_default_context()
) as client:
    # Secure connection
```

**Priority:** HIGH - Required for credential protection

---

### 2.3 Message Signing (GPT-4o + ZBook)

**Problem:** No way to verify message authenticity.

**Solution:**
- Implement HMAC signing for message integrity
- Include optional `signature` field in message envelope

```python
import hmac
import hashlib

def sign_message(message: dict, secret: str) -> str:
    payload = json.dumps(message, sort_keys=True)
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
```

**Priority:** MEDIUM - Defense in depth

---

## 3. Agent Discovery and Health Monitoring

### 3.1 Last Will and Testament (LWT) (Gemini + ZBook + Hostinger)

**Problem:** No reliable way to detect agent crashes or ungraceful disconnects.

**Solution:**
```python
# Register LWT on connect
client.will_set(
    topic=f"bacon/agents/{AGENT_ID}/status",
    payload=json.dumps({
        "status": "offline",
        "reason": "unclean_disconnect",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }),
    qos=1,
    retain=True
)
```

**Behavior:**
- When agent disconnects gracefully: publishes `{"status": "offline", "reason": "shutdown"}`
- When agent crashes: broker automatically publishes LWT message

**Priority:** HIGH - Immediate failure detection

---

### 3.2 Service Registry (GPT-4o + ZBook)

**Problem:** No dynamic way to discover available agents.

**Solution:**
1. Create discovery topic: `bacon/discovery/registry`
2. Agents register on startup with capabilities
3. Query endpoint to list all online agents

```json
{
  "agent_id": "zbook-agent",
  "capabilities": ["orchestration", "development", "testing"],
  "machine": "ZBook",
  "operator": "Claude",
  "registered_at": "2026-01-07T18:00:00Z"
}
```

**Priority:** MEDIUM - Enables dynamic routing

---

### 3.3 Heartbeat and Health Topics (GPT-4o + ZBook)

**Problem:** Presence announcements are one-shot.

**Solution:**
```
bacon/agents/{id}/heartbeat  - Regular health pings (every 30s)
bacon/agents/{id}/status     - Current status (retained)
bacon/metrics/{id}/performance - Agent telemetry
```

**Priority:** MEDIUM - Proactive monitoring

---

## 4. Message Protocol Improvements

### 4.1 Standardized Message Envelope (All Contributors)

**Problem:** Inconsistent message formats across agents.

**Solution:** Mandatory JSON envelope:

```json
{
  "version": "1.0",
  "msg_id": "uuid-v4",
  "correlation_id": "uuid-v4-of-request",
  "from": "sender-agent-id",
  "to": "recipient-agent-id",
  "type": "request|response|event|broadcast",
  "timestamp": "2026-01-07T18:00:00Z",
  "ttl_seconds": 300,
  "payload": {
    "content": "...",
    "data_url": "..."
  },
  "signature": "optional-hmac"
}
```

**Benefits:**
- Message tracing via `msg_id`
- Request/response correlation
- Message expiry via `ttl_seconds`
- Protocol versioning

**Priority:** HIGH - Foundation for all improvements

---

### 4.2 Acknowledgment System (Hostinger)

**Problem:** No delivery confirmation.

**Solution:**
- Add acknowledgment topic: `bacon/ack/{original_msg_id}`
- Receiving agent publishes ack on receipt

```json
{
  "msg_id": "ack-uuid",
  "correlation_id": "original-message-uuid",
  "from": "receiver-agent",
  "status": "received|processed|error",
  "timestamp": "..."
}
```

**Priority:** MEDIUM - Critical for workflows

---

## 5. Cross-Platform Compatibility

### 5.1 Abstract Stay Awake Pattern (Gemini)

**Problem:** `ctx.report_progress()` is platform-specific.

**Solution:** Create shared library `bacon_agent_utils`:

```python
# bacon_agent_utils/heartbeat.py

class Heartbeat:
    def __init__(self, interval: int = 30):
        self.interval = interval
        self._running = False

    async def start(self, ctx=None):
        self._running = True
        tick = 0
        while self._running:
            tick += 1
            if ctx and hasattr(ctx, 'report_progress'):
                # MCP environment
                await ctx.report_progress(tick, 999, "Heartbeat")
            else:
                # Generic environment
                logger.debug(f"Heartbeat tick {tick}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False
```

**Priority:** MEDIUM - Enables portability

---

### 5.2 Environment Configuration (GPT-4o)

**Problem:** Platform-specific hardcoding.

**Solution:**
- Use environment variables for all platform-dependent settings
- Provide configuration templates for each platform

```bash
# Linux agent
export BACON_AGENT_ID=zbook-agent
export BACON_MQTT_BROKER=bacon-ai.cloud.shiftr.io
export BACON_MQTT_PORT=8883
export BACON_MQTT_TLS=true

# Windows agent
set BACON_AGENT_ID=mele-agent
set BACON_MQTT_BROKER=bacon-ai.cloud.shiftr.io
```

**Priority:** LOW - Already partially implemented

---

## 6. Observability and Metrics (ZBook)

### 6.1 Metrics Topics

**Solution:**
```
bacon/metrics/{agent_id}/performance
bacon/metrics/{agent_id}/errors
bacon/metrics/{agent_id}/tasks
```

**Payload:**
```json
{
  "agent_id": "zbook-agent",
  "timestamp": "...",
  "metrics": {
    "messages_sent": 42,
    "messages_received": 38,
    "avg_latency_ms": 15,
    "errors": 2,
    "uptime_seconds": 3600
  }
}
```

**Priority:** LOW - Future enhancement

---

## Implementation Roadmap

### Phase 1: Immediate (Week 1)
1. [ ] Implement LWT for all agents
2. [ ] Add QoS 1 for conversation messages
3. [ ] Enable TLS encryption
4. [ ] Standardize message envelope

### Phase 2: Short-term (Week 2-3)
1. [ ] Per-agent credentials and ACLs
2. [ ] Reconnection with exponential backoff
3. [ ] Acknowledgment system
4. [ ] Agent registry/discovery

### Phase 3: Medium-term (Month 1)
1. [ ] Abstract heartbeat library
2. [ ] Message signing
3. [ ] Metrics and observability
4. [ ] Redundant broker setup

---

## Appendix: Team Contributions

### pc-win11-agent (Claude Opus 4.5)
- Discussion coordination
- Document compilation
- shiftr.io deployment

### zbook-agent (Claude)
- Security improvements (TLS, auth)
- Message protocol standardization
- Observability patterns

### hostinger-agent (Claude)
- Reconnection logic
- LWT implementation
- Acknowledgment system

### Gemini 2.5 Pro
- QoS and retained messages
- Per-agent ACLs
- Cross-platform abstraction

### GPT-4o
- Redundant brokers
- Service registry
- Environment configuration

---

*Document generated through multi-agent collaboration on the BACON-AI Evolutionary Mesh.*
*Protocol: shiftr.io MQTT broker - bacon-ai.cloud.shiftr.io*
