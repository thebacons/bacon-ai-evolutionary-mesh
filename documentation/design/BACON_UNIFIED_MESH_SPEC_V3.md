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

### 2.1 Reliability Layers
- **QoS 1 (Standard)**: All conversation messages MUST use QoS 1 to ensure delivery.
- **QoS 2 (Critical)**: Used for orchestration signals (WAKE, SHUTDOWN, TASK_ASSIGN).
- **LWT (Last Will & Testament)**: Mandatory registration on connect.
  - Topic: `bacon/agents/{id}/status`
  - Payload: `{"status": "offline", "reason": "unclean_disconnect"}`
- **Retained Presence**: `bacon/agents/{id}/presence` MUST be retained so the mesh materializes instantly for new dashboard users.

### 2.2 Standardized Message Envelope
All communication MUST follow this JSON structure:
```json
{
  "version": "3.0",
  "msg_id": "uuid-v4",
  "correlation_id": "uuid-request-id",
  "from": "sender-id",
  "to": "target-id|broadcast",
  "type": "conversation|signal|memory|heartbeat",
  "timestamp": "ISO-8601-UTC",
  "payload": {
    "content": "...",
    "metadata": {}
  }
}
```

### 2.3 Resilient Transport
- **Exponential Backoff**: Agents MUST implement `min(1 * 2^attempts, 60s)` reconnection logic.
- **TLS 1.3**: Mandatory for all environments beyond Local-Dev (Port 8883).

---

## 3. Visual Design (The "Bioluminescent" UI)
*Consolidated from Phase 3 Proposal & Benchmarking*

### 3.1 Node Morphology (State Visualization)
| State | Visual Trigger | UI Representation |
|-------|----------------|-------------------|
| **Active** | Heartbeat received < 30s ago | Solid glassmorphic node, glowing outer 'aura', pulsing. |
| **Sleeping** | Explicit Sleep Signal / No beat | Monochrome wireframe ("Ghost" node). |
| **Processing**| Message sent/received activity | "Breathing" animation (size fluctuations proportional to traffic). |
| **Offline** | LWT received | Fades to 30% opacity, persists for 60s before removal. |

### 3.2 Dynamic Flow (Message Traffic)
- **Data Packets**: Animated glowing bits traveling along links.
- **Flow Colors**:
  - `Cyan`: Standard messages.
  - `Gold`: Control signals (Signals that wake or task agents).
  - `Purple`: Memory writes (Packets traveling to the Mem0-connected Control Plane).

### 3.3 Semantic Hubs & Nebulas
- **Logical Clustering**: Agents with shared capabilities (e.g., `orchestration`) are pulled closer by higher link strengths.
- **Nebula Shading**: A faint colored background region ("Nebula") appears behind clusters of agents working on the same Topic/Mission.

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
