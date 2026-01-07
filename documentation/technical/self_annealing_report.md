# BACON-AI: Self-Annealing Report (Release 2.0)

This report documents the failure modes and critical optimizations discovered during the deployment and refinement of the Evolutionary Mesh dashboard.

## 1. Environment-Specific API Failures

### 1.1 `window.crypto.randomUUID`
*   **Issue:** Dashboard failed to render (blank screen) on `srv906866.hstgr.cloud:8000` because `randomUUID` is restricted to secure contexts (HTTPS). Hostinger deployment is currently HTTP.
*   **Self-Annealing Directive:** Always include a `Math.random` based UUID fallback in the `index.html` header and `App.tsx` logic.

### 1.2 `d3AlphaTarget`
*   **Issue:** Browser subagent and specific browser builds reported `TypeError: d3AlphaTarget is not a function` on the graph component reference.
*   **Self-Annealing Directive:** Use feature detection for D3 component methods. Fall back to standard simulation accessors (`fg.d3Simulation().alphaTarget()`) if the high-level prop is unavailable.

## 2. Code Integrity and Workflow

### 2.1 JSX Corruption in Large Files
*   **Issue:** Massive edits in files >1000 lines (like `App.tsx`) frequently resulted in unbalanced delimiters and broken closing braces, failing the build.
*   **Self-Annealing Directive:** Decompose large component edits into multiple targeted `ReplacementChunk` objects. For React components, always verify the final brace-count/nesting logic before completing a task.

## 3. User Experience and Physics

### 3.1 Nomenclature Alignment
*   **Insight:** Technical terms like "Repulsion" and "Tension" confuse users during mesh tuning.
*   **Optimization:** Remap to "Push", "Reach", and "Stiffness".

### 3.2 Live Physics Reheat
*   **Insight:** Mesh feels non-responsive during slider adjustment if the simulation is cooled (alpha=0).
*   **Optimization:** Use `onPointerDown`/`onPointerUp` to set `alphaTarget(0.3)` during active dragging, providing immediate visual feedback.

---
*Verified and Recorded in Mem0 Cloud (user_id: antigravity-agent)*
