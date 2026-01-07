# BACON-AI Mesh Join & Integration Guide

Use the following prompt in a new Claude-Code session on your **Zbook** or **Windows 11 PC**. This provides the necessary architectural context for that agent to join the Evolutionary Mesh.

---

**Prompt for the Node Agent:**

"I need you to join this machine to the **BACON-AI Evolutionary Mesh**. The Control Plane and MQTT Broker are stable at `srv906866.hstgr.cloud:8000/1883`.

### 1. Architectural Context
- **Your Role**: You are a **Resident Node Agent** (e.g., `zbook-agent` or `pc-win11-agent`).
- **My Role (Gemini/Lead)**: I am the Lead Orchestrator driving the mesh design. We are collaborating on a self-annealing system.
- **Reference**: Read `documentation/deployment/walkthrough.md` for the current protocol and success criteria.

### 2. Implementation Steps
1.  **Environment Setup**:
    *   Create a Python virtual environment.
    *   Install `aiomqtt`, `fastapi`, `sqlmodel`, and `mem0ai`.
    *   **CRITICAL**: If on Windows, ensure your `asyncio` loop policy uses `SelectorEventLoopPolicy` for `aiomqtt` compatibility (see `src/control_plane/simulate_heartbeat.py`).
2.  **Credential Sync**:
    *   Populate a local `.env` with:
        ```text
        MQTT_BROKER=srv906866.hstgr.cloud
        MQTT_PORT=1883
        MEM0_API_KEY=m0-TqhAnGlqmJt3Gr6SaJ8z5iaPWYVcGxpiI67XC4Xo
        ```
3.  **Presence Heartbeat**:
    *   Implement and run a `heartbeat.py` script.
    *   Publish a v1.2 presence message to `bacon/v1/presence/agent/[MACHINE_NAME]`.
4.  **Verification**:
    *   Confirm your registration: `curl http://srv906866.hstgr.cloud:8000/api/agents`.
5.  **Signal Integration**:
    *   Launch a persistent listener for the `WAKE` signal at `bacon/v1/signal/[MACHINE_NAME]`.

### 3. Testing Scope (Option D + B)
- Run the **Full Test Suite** (`python src/control_plane/test_mqtt.py`) to verify local environment integrity.
- Once registered, report your 'active' status and I will coordinate with the Lead Orchestrator to verify your connection."

---
