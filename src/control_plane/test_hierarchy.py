import asyncio
import json
import os
from datetime import datetime, timezone
import aiomqtt
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MQTT_BROKER: str = "srv906866.hstgr.cloud"
    MQTT_PORT: int = 1883
    MQTT_USER: str = "bacon"
    MQTT_PASS: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

async def send_hierarchy_heartbeat():
    # 1. PHYSICAL HOSTS
    remote_host = "srv906866.hostinger"
    local_host = "pc-win11"
    
    # 2. REMOTE CLUSTER (Management Layer on Hostinger)
    orchestrator_payload = {
        "v": "1.2",
        "agent_id": "mesh-orchestrator-main",
        "node_id": remote_host,
        "ts": datetime.now(timezone.utc).isoformat(),
        "state": "active",
        "meta": {
            "operator": "BACON System Manager",
            "capabilities": ["registry", "routing"]
        }
    }

    health_payload = {
        "v": "1.2",
        "agent_id": "mqtt-health-monitor",
        "node_id": remote_host,
        "ts": datetime.now(timezone.utc).isoformat(),
        "state": "active",
        "meta": {
            "operator": "Service Monitor",
            "capabilities": ["health-checks", "uptime"]
        }
    }

    # 3. LOCAL CLUSTER (Resident Layer on pc-win11)
    # The Assistant (Antigravity) is now locally linked
    gemini_payload = {
        "v": "1.2",
        "agent_id": "antigravity-brain-local",
        "node_id": local_host,
        "ts": datetime.now(timezone.utc).isoformat(),
        "state": "active",
        "meta": {
            "operator": "Antigravity (Gemini)",
            "capabilities": ["reasoning", "local-exec"]
        }
    }

    # Claude as the Primary Session
    claude_payload = {
        "v": "1.2",
        "agent_id": "claude-sonnet-dev",
        "node_id": local_host,
        "ts": datetime.now(timezone.utc).isoformat(),
        "state": "active",
        "meta": {
            "operator": "Claude (Sonnet 3.5)",
            "capabilities": ["software-dev"]
        }
    }

    # A Sub-Agent nested under Claude (Logical Hosting)
    sub_agent_payload = {
        "v": "1.2",
        "agent_id": "claude-sub-researcher",
        "node_id": "claude-sonnet-dev", # Hosted by Claude
        "parent_id": "claude-sonnet-dev",
        "ts": datetime.now(timezone.utc).isoformat(),
        "state": "active",
        "meta": {
            "operator": "Research-Agent-01",
            "capabilities": ["knowledge-discovery"]
        }
    }

    print("🚀 Publishing Mirror Topology (Local + Remote Segregation)...")
    
    try:
        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            username=settings.MQTT_USER,
            password=settings.MQTT_PASS
        ) as client:
            # Publish all
            payloads = [
                (orchestrator_payload, "bacon/v1/presence/agent/mesh-orchestrator-main"),
                (health_payload, "bacon/v1/presence/agent/mqtt-health-monitor"),
                (gemini_payload, "bacon/v1/presence/agent/antigravity-brain-local"),
                (claude_payload, "bacon/v1/presence/agent/claude-sonnet-dev"),
                (sub_agent_payload, "bacon/v1/presence/agent/claude-sub-researcher")
            ]
            for p, topic in payloads:
                await client.publish(topic, payload=json.dumps(p))
        print("✅ Mirror Topology heartbeats sent!")
    except Exception as e:
        print(f"❌ Failed: {e}")

async def send_signals():
    print("📡 Sending Virtual Signal traffic...")
    try:
        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            username=settings.MQTT_USER,
            password=settings.MQTT_PASS
        ) as client:
            # 1. Claude (Local) -> Orchestrator (Remote) : "Asking"
            msg1 = {
                "type": "signal",
                "source": "claude-sonnet-dev",
                "content": {"type": "WAKE", "reason": "Querying remote registry"},
                "ts": datetime.now(timezone.utc).isoformat()
            }
            await client.publish("bacon/v1/signal/agent/mesh-orchestrator-main", payload=json.dumps(msg1))
            
            # 2. Orchestrator (Remote) -> Claude (Local) : "Answering"
            msg2 = {
                "type": "signal",
                "source": "mesh-orchestrator-main",
                "content": {"type": "DATA", "reason": "Returning registry subset"},
                "ts": datetime.now(timezone.utc).isoformat()
            }
            await client.publish("bacon/v1/signal/agent/claude-sonnet-dev", payload=json.dumps(msg2))

            # 3. Local Researcher -> Local Claude : "Reporting"
            msg3 = {
                "type": "signal",
                "source": "claude-sub-researcher",
                "content": {"type": "UPDATE", "reason": "Task complete"},
                "ts": datetime.now(timezone.utc).isoformat()
            }
            await client.publish("bacon/v1/signal/agent/claude-sonnet-dev", payload=json.dumps(msg3))
            
        print("✅ Signal traffic simulated!")
    except Exception as e:
        print(f"❌ Failed signals: {e}")

async def main():
    await send_hierarchy_heartbeat()
    await asyncio.sleep(1) # Wait for heartbeat to process
    await send_signals()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
