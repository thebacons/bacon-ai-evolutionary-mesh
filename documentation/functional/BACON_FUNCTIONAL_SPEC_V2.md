# BACON-AI Release 2.0: Functional Specification

**Date:** 2026-01-05
**Version:** 2.0
**Status:** Draft

## 1. Scope
System logic for the "BACON-AI Command Center" deployed on `srv906866.hstgr.cloud`, and the Client Daemons running on distributed nodes.

## 2. Component Functions

### 2.1 Control Plane (Server)
Located on Hostinger Cloud.
*   **FN-CP-01 (Registry):** Maintain a registry of all nodes and agents (ID, Capabilities, OS).
*   **FN-CP-02 (Presence Monitor):** Track heartbeat signals. Mark agents "Offline" after 30s silence.
*   **FN-CP-03 (History & Queue):** Log all MQTT traffic. Store messages for offline agents and redeliver upon reconnection.
*   **FN-CP-04 (API):** Provide REST/WebSocket API for the Web Dashboard to consume real-time state.
*   **FN-CP-05 (Security Manager):** Validate credentials and manage MQTT ACLs.
*   **FN-CP-06 (Memory Service):** Store semantic learnings (fixes, OS quirks) using Mem0. Expose API for logic retrieval.

### 2.2 Agent Daemon (Client)
Located on Windows, ZBook, EliteBook.
*   **FN-AG-01 (Auto-Discovery):** Automatically identify host resources (RAM, CPU, Installed Tools) on startup.
*   **FN-AG-02 (Presence Loop):** Publish `bacon/v1/presence/{id}` every 10 seconds.
*   **FN-AG-03 (Signal Listener):** Listen on `bacon/v1/signal/{id}` for commands (Wake, Execute).
*   **FN-AG-04 (Safety):** Only execute commands from "Verified" senders.
*   **FN-AG-05 (Persistence):** Run as a `systemd` service on Linux and `Task Scheduler` on Windows to ensure 100% uptime.

### 2.3 Web Dashboard
Accessed via Browser.
*   **FN-DB-01 (Visual Graph):** Render nodes and links as a force-directed graph.
*   **FN-DB-02 (Live Traffic):** Visualize messages as moving particles on links.
*   **FN-DB-03 (Metrics):** Display global system health (Active Agents, Messages/Min).
*   **FN-DB-04 (Remote Terminal):** Execute shell commands on remote nodes via the secure MQTT signal path.

## 3. High-Level Roadmap: Multi-Model Orchestration & Evolution
*   **Task Routing:** Auto-route "Coding" tasks to Claude, "Reasoning" to GPT-5/Gemini, and "Sensitive" data to local Ollama clusters.
*   **The Evolutionary Loop (Phase 5):**
    *   **The Mechanic Agent:** Monitors error logs + Mem0; auto-suggests or applies patches to client daemons.
    *   **The Scout Agent:** Monitors the AI frontier. Favors **Push-Models** (RSS, GitHub Webhooks, API change logs) over expensive daily pulls. Triggers monthly depth-scans to suggest tech-stack upgrades.
    - **The Architect Agent:** The "Metacognitive" layer.
        - **Internal Focus:** Analyzes usage patterns to propose schema migrations.
        - **Observational Triage:** Can "intervene" in complex agent-to-agent conversations to provide triage or sanity-check architectural paths before execution.
*   **Human-In-The-Loop (HITL):** All "Evolutionary Recommendations" are queued in the Dashboard for human review before execution.

## 3. Data Requirements
*   **Agent Identity:** Unique ID (UUID or `hostname-role`), Display Name, Capabilities List.
*   **Message Object:** Standard JSON envelope (as defined in Technical Spec).
*   **Persistence:** Server must retain logs for at least 7 days.

## 4. References
*   [Process Design](../process/PROCESS_DESIGN.md)
*   [Technical Specification](../technical/TECHNICAL_SPEC.md)
