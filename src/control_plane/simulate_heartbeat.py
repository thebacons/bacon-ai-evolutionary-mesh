import asyncio
import json
import os
import aiomqtt
import sys
from datetime import datetime, timezone

# Fix for Windows asyncio NotImplementedError with aiomqtt
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

MQTT_BROKER = "srv906866.hstgr.cloud"
MQTT_PORT = 1883
TOPIC = "bacon/v1/presence/agent/pc-win11-agent"

payload = {
    "v": "1.2",
    "agent_id": "pc-win11-agent",
    "node_id": "pc-win11",
    "ts": datetime.now(timezone.utc).isoformat(),
    "state": "active",
    "meta": {
        "operator": "Claude (Sonnet 3.5)",
        "task_current": "Verification Simulation",
        "queue_depth": 0
    },
    "capabilities": ["orchestration", "testing"]
}

async def run_test():
    print(f"🚀 Publishing presence to {TOPIC}...")
    async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
        await client.publish(TOPIC, json.dumps(payload))
    print("✅ Heartbeat sent!")

if __name__ == "__main__":
    asyncio.run(run_test())
