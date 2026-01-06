# BACON-AI Release 2.0: Process Design Document

**Date:** 2026-01-05
**Version:** 2.0
**Status:** Draft

## 1. Introduction
This document defines the core business processes and workflows for the BACON-AI Multi-Agent System. It uses BPMN-style descriptions to illustrate how agents, the control plane, and humans interact.

## 2. Core Processes

### 2.1 Agent Registration & Startup (BPMN)
**Actors:** Agent (Client), Control Plane (Server), Broker.

1.  **Start Event:** Agent Daemon starts on Host Node (Windows/Linux).
2.  **Task:** Agent generates/loads Identity (`agent_id`, `capabilities`).
3.  **Task:** Agent connects to MQTT Broker (`srv906866.hstgr.cloud:1883`).
4.  **Gateway (Connectivity):**
    *   *Success:* Proceed.
    *   *Failure:* Retry with exponential backoff.
5.  **Message Flow:** Agent publishes `bacon/v1/presence/{id}` (Status: ONLINE).
6.  **Task (Server):** Control Plane detects new Presence message.
7.  **Task (Server):** Control Plane updates `agents` table in Database.
    *   *If new:* Create record.
    *   *If existing:* Update `last_seen` and `capabilities`.
8.  **End Event:** Agent is visible on Dashboard.

### 2.2 Task Delegation Workflow
**Actors:** Coordinator Agent (e.g., Windows), Worker Agent (e.g., ZBook), Control Plane.

1.  **Start Event:** Coordinator needs to offload a task (e.g., "Check Docker").
2.  **Task:** Coordinator consults `bacon/v1/presence/+` (or queries Control Plane API).
3.  **Decision:** Identify best available agent with `docker` capability.
4.  **Message Flow:** Coordinator publishes `bacon/v1/signal/{worker_id}` (Type: TASK).
5.  **Task (Worker):** Worker Agent receives signal.
6.  **Task (Worker):** Worker spawns "Shadow Agent" (Sub-process) to handle request.
7.  **Task (Shadow):** Executes Docker check.
8.  **Message Flow:** Shadow publishes `bacon/v1/data/{coordinator_id}` (Result).
9.  **End Event:** Coordinator receives result; Shadow terminates.

### 2.3 Human Intervention (Dashboard)
**Actors:** Human User, Web Dashboard, Control Plane.

1.  **Start Event:** User views Dashboard.
2.  **Task:** User clicks "Wake Agent" on ZBook node.
3.  **Message Flow:** Dashboard sends WebSocket command to Control Plane.
4.  **Task (Server):** Control Plane runs permission check.
5.  **Message Flow:** Control Plane publishes `bacon/v1/signal/zbook` (Type: WAKE).
6.  **Task (Agent):** ZBook Agent receives WAKE.
7.  **Task (Agent):** Trigger `tmux` wake script.
8.  **End Event:** ZBook session transitions to ACTIVE state.

## 3. Use Cases

| ID | Title | Actor | Description |
| :--- | :--- | :--- | :--- |
| **UC-01** | **Global Observability** | Human | View all active agents, their health (RAM/CPU), and current tasks on a single webmap. |
| **UC-02** | **Cross-OS Orchestration** | Agent | A Windows agent triggers a heavy compilation job on the Linux server without user intervention. |
| **UC-03** | **Context Transfer** | Agent | An agent "passes the baton" (Session Capsule) to another agent to continue a conversation. |
| **UC-04** | **Skills Discovery** | Agent | An agent queries the Control Plane to find "Who knows about Python?" and routes a query to them. |

## 4. References
*   [Technical Specification](../technical/TECHNICAL_SPEC.md)
*   [Functional Specification](../functional/FUNCTIONAL_SPEC.md)
