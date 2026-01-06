# BACON-AI Release 2.0 Implementation Plan

**Objective:** Deploy the "Command Center" to the Hostinger Cloud Server and connect distributed agents.

## Phase 1: Server-Side Foundation (Hostinger)
**Goal:** Establish the Brain.

### 1.1 Infrastructure Prep
- [x] Identify Hostinger Server (`srv906866.hstgr.cloud`).
- [ ] Verify Mosquitto is running/accessible.
- [ ] Install Python 3.10+ and `pip` if missing.

### 1.2 Control Plane Deployment (PoC)
- [ ] Implement `main.py` (FastAPI + MQTT Loop) - Auth optional/disabled for now.
- [ ] Implement `database.py` (SQLite backend).
- [ ] Deploy code to Server (`/home/bacon/bacon-control-plane`).
- [ ] Setup `systemd` service (`bacon-control.service`).

### 1.3 Memory Gateway (Self-Annealing)
- [ ] Initialize `Mem0` client in the Control Plane.
- [ ] Implement `/memory/learn` and `/memory/recall` endpoints.
- [ ] Record initial "System Quirk" memories (e.g., Hostinger's default Python version).

## Phase 2: Client-Side Universal Agent
**Goal:** Create a specific, OS-agnostic agent daemon.

### 2.1 Universal Agent & Persistence
- [ ] Create universal `agent_daemon.py` (adopting the tested `bacon_mqtt_mcp` package structure).
- [ ] Implement presence loop with authenticated MQTT.
- [ ] **Systemd Integration:** Create and enable `bacon-mqtt-listener.service`.
- [ ] Verify on **Windows** using Task Scheduler or background script.

### 2.2 Client Rollout
- [ ] Deploy to **ZBook** and **EliteBook**.
- [ ] Verify global connectivity.

## Phase 3: The Command Center (Dashboard)
**Goal:** Visual observability.

### 3.1 GUI Dashboard Construction
- [ ] Create `documentation/functional/GUI_DASHBOARD_DESIGN.md`.
- [ ] Build React Dashboard base with `react-force-graph`.
- [ ] Implement shiftr.io style particle animations for data flow.
- [ ] Serve via FastAPI on the cloud server.

### 3.2 Interaction & Control
- [ ] Connect WebSocket feed to the Graph.
- [ ] Implement the "Inspector" sidebar for agent capabilities.
- [ ] Add manual "Wake" trigger from the GUI.

## Phase 4: Production Hardening (SIT-2)
**Goal:** Transition from PoC to Secure Release.

### 4.1 MQTT Security Enablement
- [ ] Enable Mosquitto Username/Password authentication.
- [ ] Update Control Plane & Agents to use `MQTT_USER`/`MQTT_PASS`.
- [ ] Run **SIT-2 Regression Suite** to ensure no breakages.
- [ ] (Optional) Enable TLS/SSL on Port 8883.
