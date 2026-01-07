# BACON-AI Phase 3: "Neural Mesh" UI Design Proposal

**Codename:** *Radiance*
**Focus:** Semantic visualization, Attention-driven UI, and Interactive Orchestration.

## 1. Aesthetic Shift: The "Glass Neural" Theme
Instead of a flat dashboard, Phase 3 will adopt a **High-Conjunction Neural Network** look. 

- **Background**: Deep Indigo/Black gradients with a subtle moving grid (`radial-gradient`).
- **Nodes**: Glassmorphism effect (frosted translucency) with glowing borders colored by Agent Group.
- **Typography**: Space-efficient monospaced fonts for technical data (JetBrains Mono) paired with clean sans-serifs (Outfit/Inter) for headings.

## 2. Presence-Driven Morphology (Visual Feedback)
The UI should reflect the *state* of the agent, not just its existence.

| Agent State | Visual Representation |
|-------------|-----------------------|
| **Active** | Brighter glow, slow pulsing outer ring, visible "attention" link to current task. |
| **Idle** | Steady, dimmed glow. |
| **Sleeping** | Wireframe/Outline only, monochrome (grayscale), particle flow stops. |
| **Busy/Crunching**| Fast vibrating ring, secondary "thought" particles orbiting the node. |
| **Degraded** | Red flickering border, static-like visual distortion. |

## 3. Communication Visualization (The Flow)
Inspired by shiftr.io but enhanced for semantic meaning.

- **Data Packets**: Animated "bits" (small squares or glowing dots) that travel between nodes.
- **Packet Coloring**: 
    - *Cyan*: Standard communication.
    - *Gold*: Critical "Signal" or "Instruction".
    - *Purple*: Memory being saved (moving towards the central Control Plane hub).
- **Link Elasticity**: Links between agents that communicate frequently should become thicker and more "tense," pulling the nodes closer together (dynamic link strength).

## 4. Semantic Hubs (Topic Anchors)
Agents should cluster around **Logical Topics** (e.g., `orchestration`, `vision`, `memory`).
- High-level topics are depicted as "Gravity Wells" or "Hubs" in the center of the screen.
- Agents orbit their primary topic, creating natural visual clusters.

## 5. Contextual Action HUD (Interactivity)
Clicking a node shouldn't just show data; it should open a circular **Action HUD** around the node:
- **[WAKE]**: Send MQTT wake-up signal (tmux injection).
- **[SENSE]**: Open real-time terminal stream from that agent.
- **[MEM]**: Overlay recent semantic memories from Mem0 as "floating wisps" around the node.
- **[SIGNAL]**: Quick-send common commands (Status, Restart, Ping).

## 6. Implementation Strategy
- **Visualizer**: Upgrade to `react-force-graph-3d` or use custom `canvas` overrides in `2d` for performance.
- **State Management**: Integrate a more robust WebSocket/MQTT bridge that pipes high-resolution "Attention" events to the UI.
- **Particles**: Use a lightweight particle system (like `pixi.js` or `canvas-confetti` principles) that hooks into the link rendering cycle.

---
*Created by Antigravity (Gemini) for the BACON-AI Evolutionary Mesh Project.*
