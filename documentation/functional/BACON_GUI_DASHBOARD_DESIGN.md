# BACON-AI Release 2.0: GUI & Dashboard Design

**Date:** 2026-01-06
**Version:** 1.0
**Inspirations:** [shiftr.io](https://shiftr.io), [robotmaker.eu](https://robotmaker.eu), `mqtt-agent-sim`

## 1. Design Philosophy
The Dashboard is more than a display; it is a **live organism**. It uses physics-based animations to represent the health and activity of the agent mesh.

*   **Real-time Observability:** Every MQTT packet is visible as a particle.
*   **Organic Connectivity:** Nodes drift on a canvas, pulled by data relationships.
*   **Command Transparency:** Human overrides are visually distinct from automated agent signals.

## 2. Visual Language

### 2.1 The Mesh (Node-Link Graph)
Built with `react-force-graph` or `p5js`.
*   **Nodes (Agents/Nodes):**
    *   **Core Nodes:** Large pulsing circles representing physical machines (Windows, ZBook, EliteBook).
    *   **Shadow Agents:** Smaller circles tethered to their parent node, spawned for specific tasks.
    *   **States:** 
        *   `🟢 ACTIVE`: Bright green pulse.
        *   `🟡 BUSY`: Steady amber glow.
        *   `🔵 SHADOW`: Translucent blue.
        *   `⚪ IDLE`: Faded grey.
        *   `🔴 OFFLINE`: Hollow red circle (ghost node).
*   **Links (Channels):**
    *   **Width:** Proportional to the number of messages exchanged in the last 60 seconds.
    *   **Color:** Matches the target node's status.
    *   **Packets:** Small glowing particles travelling from sender to receiver upon every `bacon/v1/data` message.

### 2.2 Aesthetic Prefixes
*   **Theme:** "Deep Space Cinema" (Dark Mode).
*   **Background:** #0a0a0c with a subtle cyan grid (100px cells).
*   **Accents:** Cyber-yellow (#f2e307) and Neon-blue (#00f3ff).

## 3. Layout & Components

### 3.1 Global Navigation (Header)
*   **System Pulsar:** A small pulsing logo showing global status (OK/WARNING).
*   **Stats:** TOTAL_NODES | MSGS_PER_SEC | UPTIME.
*   **Menu:** 
    *   `Search`: Find agent by capability (e.g., "docker").
    *   `Filter`: Toggle showing/hiding Shadow agents.
    *   `Settings`: Broker Configuration (Cloud/Local).

### 3.2 Main View (The Canvas)
*   The primary interaction area.
*   **Interaction:**
    *   `Drag`: Reposition nodes (physics reacts).
    *   `Click`: Select node to open the **Inspector**.
    *   `Double-Click`: Context-aware "Wake" signal sent to idle nodes.

### 3.3 The Inspector (Right Sidebar)
Collapsible panel triggered by node selection.
*   **Identity:** Hostname, OS Icon, IP.
*   **Capabilities Tag Cloud:** List of detected skills (Docker, Python, ffmpeg, etc.).
*   **Queue Depth:** Vertical level bar showing work backlog.
*   **Actions Button:** [Wake] [Reboot Daemon] [Terminal Session].

### 3.4 Command Console (Bottom Tray)
Slide-up panel for power users.
*   **Live Trace:** Filtered MQTT log (JSON-to-human readable text).
*   **Command Input:** `> ping zbook` or `> exec all "docker ps"`.

## 4. Interaction Process Flow

1.  **User opens Dashboard.**
2.  **Dashboard connects to Control Plane WebSocket.**
3.  **Graph "explodes" into view** as registration messages are hydrated from the database.
4.  **User witnesses "Blinking" links** as agents exchange presence heartbeats.
5.  **User clicks "ZBook"** -> Sidebar slides out showing ZBook is `IDLE`.
6.  **User clicks "Wake"** -> A `bacon/v1/signal/zbook` (Type: WAKE) particle is seen moving across the screen.
7.  **Node turns `ACTIVE`** in real-time.

## 5. Benchmarking Reference
*   **shiftr.io style**: For the core graph experience.
*   **robotmaker.eu style**: For the technical "Skill Registry" and registry-based orchestration.
