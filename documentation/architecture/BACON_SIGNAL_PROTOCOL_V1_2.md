# BACON-AI Signal and Control Protocol (v1.2)
**Date:** 2026-01-05
**Status:** Draft Standard
**Validation:** Validated via `TEST_MEMO_2026-01-05.md` (Hostinger Broker)

## 1. Executive Summary
This protocol defines the "Nervous System" for the BACON-AI multi-agent ecosystem. It replaces ad-hoc file transfers with a structured, observable messaging mesh managed by a centralized **Control Plane**.

**Core Philosophy:**
> "Agents are nodes. Messages are signals. The Control Plane provides omniscience."

---

## 2. Infrastructure: The Spinal Cord
*   **Broker:** `srv906866.hstgr.cloud`
*   **Port:** `1883` (TCP)
*   **Auth:** Open (Phase 1), Username/Token (Phase 2+)
*   **Validation:** Cross-machine connectivity verified between Windows, ZBook, and EliteBook.

---

## 3. Topic Namespace
Root topic: `bacon/v1/` (Migrating from legacy `bacon/claude/`)

### 3.1 Presence (Heartbeats)
*   **Topic:** `bacon/v1/presence/agent/{agent_id}`
*   **Sender:** Agents (Daemon wrapper).
*   **Payload:**
    ```json
    {
      "v": "1.2",
      "agent_id": "windows-main",
      "node_id": "windows-pc",
      "ts": "ISO8601",
      "state": "active", // active, idle, sleeping, busy, dnd
      "meta": { 
        "task_current": "Refactoring X", 
        "queue_depth": 0 
      },
      "capabilities": ["orchestration", "gpu-compute", "docker"] // Added from Test findings
    }
    ```

### 3.2 Signals (Control Messages)
*   **Topic:** `bacon/v1/signal/{target_id}`
*   **Purpose:** Wake requests, shadow clone commands, interrupt signals.
*   **Payload:**
    ```json
    {
      "type": "WAKE" | "SHADOW_SPAWN" | "INTERRUPT",
      "requester": "zbook-supervisor",
      "priority": "high",
      "reason": "User requested database check"
    }
    ```

### 3.3 Data (Agent Communication)
*   **Topic:** `bacon/v1/data/{target_id}`
*   **Purpose:** The actual questions, answers, and context capsules.

---

## 4. Control Plane Data Model
The Control Plane maintains a **Relational Database** (Postgres/SQLite) to drive the generic UI.

### 4.1 Tables
*   **Nodes:** Hardware registries (`id`, `hostname`, `os`, `capabilities`).
*   **Agents:** Runtime instances (`id`, `node_id`, `role`, `status`, `last_seen`).
*   **Edges:** Connectivity graph (`source`, `target`, `type`).
*   **Messages:** Log of all traffic (`id`, `ts`, `from`, `to`, `payload`, `state`).

---

## 5. Dashboard Visualization Specification
The Dashboard connects via WebSocket to the Control Plane (NOT MQTT directly).

### 5.1 Visual Language
*   **Nodes:**
    *   **Server/Supervisor:** Rectangles.
    *   **Agents:** Circles.
    *   **Ephemerals (Shadows):** Hexagons or small particles.
*   **Links:**
    *   **Structural:** Solid thin lines (Owner -> Agent).
    *   **Traffic:** Animated pulses along edges (Agents <-> Agents).
*   **Colors:**
    *   `Green`: Active/Online.
    *   `Amber`: Idle/Sleeping (Ghosted).
    *   `Red`: Error/Offline.

### 5.2 Interactions
*   **Click Node:** Reveal "Inspector Panel" (DB record, recent logs).
*   **Drag Node:** Physics-based arrangement (Force Graph).
*   **Console:** "God Mode" terminal to inject MQTT signals manually.
