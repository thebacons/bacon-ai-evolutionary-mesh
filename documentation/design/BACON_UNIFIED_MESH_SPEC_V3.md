# BACON-AI: Unified Mesh Specification (v3.0)

**Codename:** *Radiance*
**Date:** 2026-01-07
**Status:** Unified Design Baseline
**Scope:** Architecture, Protocol, and Visual Logic for `bacon-ai-mqtt-mesh`.

---

## 1. Vision Statement
To create building blocks for a self-annealing, distributed multi-agent intelligence that is as visually intuitive as it is technically resilient. The mesh is not just a transport layer; it is a living organism where data flow equals vitality.

---

## 2. Technical Protocol (The "Nervous System")
*Consolidated from Team Consensus (Claude-Code, Gemini, GPT-4o)*

### 2.1 Reliability & Resilience
- **QoS 1 (Standard)**: All conversation messages MUST use QoS 1.
- **QoS 2 (Critical)**: Used for orchestration signals (WAKE, SHUTDOWN, TASK_ASSIGN).
- **LWT (Last Will & Testament)**: Mandatory registration on connect.
  - Topic: `bacon/agents/{id}/status`
  - Payload: `{"status": "offline", "reason": "unclean_disconnect"}`
- **Heartbeat & TTL**: Agents MUST send a heartbeat every 30s. A node is marked "Sleeping" after 3 missed beats and "Offline" if LWT triggers.
- **Local Queuing & Replay**: On broker disconnect, agents SHOULD buffer outgoing messages locally and replay with proper `timestamp` on reconnect.
- **Dead Letter Queues (DLQ)**: Messages failing processing after N retries MUST be routed to `bacon/dlq/{agent_id}` for audit.
- **Claims Check Pattern**: Payload objects > 64KB MUST be uploaded to a store (S3/HTTP), sending only the `data_url` and `checksum` in the MQTT message.

### 2.2 Standardized Message Envelope
All communication MUST follow this JSON structure:
```json
{
  "version": "3.0",
  "msg_id": "uuid-v4",
  "correlation_id": "uuid-v4",
  "from": "sender-id",
  "to": "recipient-id|broadcast",
  "type": "conversation|signal|memory|heartbeat|error",
  "priority": "low|normal|high|critical",
  "timestamp": "ISO-8601-UTC",
  "ttl_seconds": 300,
  "payload": {
    "content": "...",
    "metadata": {},
    "error": { "code": "TIMEOUT", "message": "...", "retryable": true }
  }
}
```

### 2.3 Security & Transport
- **TLS 1.3**: Mandatory for all environments beyond Local-Dev (Port 8883).
- **Per-Agent Credentials**: Unique JWT/Token per `agent_id`; Shared tokens are forbidden.
- **Message Signing**: (Optional) HMAC signature for cross-environment verification.

---

## 3. Visual Design (The "Bioluminescent" UI)
*Consolidated from Phase 3 Proposal & Benchmarking*

### 3.1 Node Morphology (State Visualization)
| State | Visual Trigger | UI Representation |
|-------|----------------|-------------------|
| **Active** | Heartbeat received < 30s ago | Solid glassmorphic node, glowing aura. |
| **Stability**| `payload.temperature` | Inner core glow shift: Blue (0.0, Stable) to Solar Red (1.0, Learning/Unstable). |
| **Sleeping** | 3 Missed Beats / Sleep Signal | Monochrome wireframe ("Ghost" node). |
| **Processing**| Message activity | "Breathing" animation (pulsing size fluctuations). |
| **Offline** | LWT received | Fades to 30% opacity, persists briefly for context. |

### 3.2 Dynamic Flow (Message Traffic)
- **Data Packets**: Animated glowing bits traveling along links.
- **Flow Colors**:
  - `Cyan`: Standard messages.
  - `Gold`: Control signals (Signals that wake or task agents).
  - `Purple`: Memory writes (Packets traveling to the Mem0-connected Control Plane).

### 3.3 Semantic Hubs & Nebulas
- **Logical Clustering**: Agents with shared capabilities (e.g., `orchestration`) are pulled closer by higher link strengths.
- **Timeline Scrubber**: Use a historical playback bar to review past message traffic and node states.
- **Heat Map Mode**: Toggle visibility of message density across the canvas to identify topic bottlenecks.
- **WebSockets**: The dashboard MUST use WebSocket for real-time delivery of MQTT events from the Control Plane to avoid polling overhead.

---

## 4. Interaction Model
Nodes are not just indicators; they are **Intervention Points**.
- **Context HUD**: Right-click/Long-press on a node opens a radial menu:
  - `[WAKE]`: Inject TMUX keys to wake a sleeping agent.
  - `[MEMORY]`: Stream recent Mem0 facts around the node like a "word cloud".
  - `[SIGNAL]`: Direct command injection.

---

## 5. Deployment Directory Structure
To maintain clarity across all sessions and environments:

| Path | Purpose |
|------|---------|
| **`/src/`** | Core Implementation (FastAPI, React, Daemon). |
| **`/documentation/`** | Core specs and functional requirements. |
| **`/documentation/benchmarking/`** | Research, shiftr.io logs, and design proposals. |
| **`/documentation/design/`** | Finalized UI/UX specifications. |

---
*Unified Specification derived from the collaboration of Antigravity (Gemini), Claude-Code Team, and Shiftr.io Benchmarking.*
