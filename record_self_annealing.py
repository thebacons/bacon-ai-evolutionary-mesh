import os
import sys
from dotenv import load_dotenv

# Add src/control_plane to path to import memory_gateway
sys.path.append(os.path.join(os.getcwd(), 'src', 'control_plane'))

from memory_gateway import MemoryGateway

def record_lessons():
    load_dotenv()
    gateway = MemoryGateway(user_id="antigravity-agent")
    
    lessons = [
        {
            "text": "The browser environment (Vite/React) often fails on 'window.crypto.randomUUID' in non-HTTPS or certain browser extension contexts. A robust fallback using Math.random() is required in both index.html and App.tsx.",
            "metadata": {"category": "stability", "topic": "crypto-polyfill", "severity": "high"}
        },
        {
            "text": "D3 force simulations in older or specific browser environments may not support 'd3AlphaTarget' directly on the graph component ref. Use defensive checks and fall back to the standard simulation alpha target setting.",
            "metadata": {"category": "stability", "topic": "d3-physics", "severity": "medium"}
        },
        {
            "text": "Large file edits in App.tsx (React) can lead to JSX tag corruption or broken closing braces. When modifying core UI structures, verify the JSX tree integrity before committing.",
            "metadata": {"category": "workflow", "topic": "jsx-corruption", "severity": "high"}
        },
        {
            "text": "Physics parameters are more intuitive when named: 'Push' (Repulsion), 'Reach' (Distance), and 'Stiffness' (Tension). This improves user interaction clarity.",
            "metadata": {"category": "ux", "topic": "nomenclature", "severity": "low"}
        },
        {
            "text": "For live-physics feedback during slider drags, use pointerDown/pointerUp to 'reheat' the simulation (alphaTarget(0.3)). This provides immediate visual response to parameter changes.",
            "metadata": {"category": "ux", "topic": "physics-feedback", "severity": "medium"}
        }
    ]
    
    print("🚀 Recording self-annealing lessons in Mem0...")
    for lesson in lessons:
        res = gateway.learn(lesson["text"], metadata=lesson["metadata"])
        if res:
            print(f"✅ Learned: {lesson['metadata']['topic']}")
        else:
            print(f"❌ Failed to learn: {lesson['metadata']['topic']}")

if __name__ == "__main__":
    record_lessons()
