# BACON-AI Release 2.0: Technical Specification

**Date:** 2026-01-05
**Version:** 2.0
**Status:** Draft

## 1. System Architecture
Client-Server model leveraging MQTT for real-time mesh communication.

### 1.1 Stack
*   **Server (Hostinger):**
    *   OS: Ubuntu 24.04 LTS
    *   Broker: Mosquitto (Port 1883)
    *   Control Plane: Python 3.10+ (FastAPI, SQLModel, Paho-MQTT)
    *   Database: SQLite (`bacon.db`) for Node Registry and Message Queuing.
    *   Memory Layer: Mem0 (Semantic context and self-annealing).
    *   Process Manager: Systemd (for auto-start and persistence).
*   **Client (Nodes):**
    *   Language: Python 3.10+
    *   Libraries: `bacon-mqtt-mcp` (custom package), `aiomqtt`, `mcp`, `edge-tts`

## 2. Data Models (Schema)

### 2.1 Database Schema (SQLModel)
```python
class Agent(SQLModel, table=True):
    id: str = Field(primary_key=True)
    hostname: str
    capabilities: str # JSON string
    last_seen: datetime
    status: str

class MessageLog(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    timestamp: datetime
    sender_id: str
    target_id: str
    topic: str
    payload: str # JSON string
```

### 2.2 MQTT Payload Specification
Confirms to `BACON_SIGNAL_PROTOCOL.md` (v1.2).

## 3. API Specification (Control Plane)

### 3.1 REST Endpoints
*   `GET /api/agents` - List all seen agents.
*   `GET /api/history?limit=100` - Get recent messages.
*   `POST /api/signal` - Inject a signal (Wake/Command).
*   `GET /api/memory/{agent_id}` - Retrieve semantic memories for a node.
*   `POST /api/memory/learn` - Manually inject a semantic memory.


### 3.2 WebSocket
*   `ws://server/ws/feed` - Push updates for Dashboard.
    *   Event: `AGENT_UPDATE`
    *   Event: `MESSAGE_NEW`

## 4. Deployment Strategy

### 4.1 Server Deployment
Deployed to `srv906866.hstgr.cloud` via SSH.
```bash
/home/bacon/bacon-stack/
  ├── venv/
  ├── main.py
  ├── database.db
  └── static/ (React Build)
```

### 4.2 Client Deployment
Deployed to agents via Git/SCP.
```bash
~/bacon-agent/
  ├── agent_daemon.py
  ├── config.json (Broker URL, Agent ID)
  └── capabilities.json
```

## 5. Security Hardening
*   **Authentication:** Username/Password auth required for all MQTT connections (MQTT_USER, MQTT_PASS).
*   **Access Control:** Anonymous access disabled on Mosquitto broker.
*   **TLS Encryption:** Transition to Port 8883 with SSL/TLS certificates for all cross-network traffic (Planned for Phase 1.2).

## 6. Message Persistence & Reliability
*   **Offline Handling:** When an agent publishes to an offline target, the Control Plane caches the message in the `MessageLog` table with a `delivered=False` flag.
*   **Contextual Memory (Mem0):** The Control Plane maintains a semantic memory of system errors and manual fixes.
*   **External Signal Integration:** Roadmap support for **Webhook Listeners** (GitHub/RSS) to allow the "Scout" agent to receive push notifications.
*   **Retry Logic:** Control Plane re-emits pending messages when a target's `presence` becomes `ACTIVE`.
*   **Progress Notifications:** Any blocking `wait_for_message` call MUST emit progress ticks every 30s to prevent MCP timeout (SIT-verified pattern).

## 7. References
*   [Process Design](../process/PROCESS_DESIGN.md)
*   [Functional Specification](../functional/FUNCTIONAL_SPEC.md)
*   [Existing Architecture](../../architecture/ADD.md) (Legacy Context)
