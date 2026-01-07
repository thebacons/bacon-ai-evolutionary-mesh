import os
import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from database import init_db, get_session
from models import Agent, Message, Node
from mqtt_handler import MQTTHandler
from memory_gateway import MemoryGateway

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bacon-control-plane")

# Configuration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "srv906866.hstgr.cloud")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")

app = FastAPI(title="BACON-AI Control Plane")
mqtt = MQTTHandler(MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS)
memory = MemoryGateway()

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Initializing Control Plane database...")
    asyncio.create_task(presence_monitor())
    asyncio.create_task(signal_monitor())

async def signal_monitor():
    """Background task to monitor agent signal messages."""
    logger.info("Starting Signal Monitor...")
    # Matches bacon/v1/signal/agent/{target}
    topic = "bacon/v1/signal/agent/+"
    
    async def handle_signal(topic: str, payload: dict):
        try:
            # Topic format: bacon/v1/signal/agent/target_id
            target = topic.split("/")[-1]
            # Payload envelope usually has 'source' from MQTTHandler.publish
            # Content of signal is usually in 'content' if sent via mqtt.publish
            content = payload.get("content", {}) if isinstance(payload.get("content"), dict) else payload
            sender = payload.get("source") or content.get("requester") or "unknown"
            
            with get_session() as session:
                log = Message(
                    sender=sender,
                    target=target,
                    topic=topic,
                    payload=json.dumps(payload),
                    state="delivered"
                )
                session.add(log)
                session.commit()
        except Exception as e:
            logger.error(f"Error handling signal message: {e}")

    await mqtt.listen(topic, handle_signal)

async def presence_monitor():
    """Background task to monitor agent presence signals."""
    logger.info("Starting Presence Monitor...")
    topic = "bacon/v1/presence/agent/+" 
    
    async def handle_presence(topic: str, payload: dict):
        try:
            agent_id = payload.get("agent_id")
            node_id = payload.get("node_id")
            parent_id = payload.get("parent_id")
            capabilities = json.dumps(payload.get("capabilities", []))
            state = payload.get("state", "unknown")
            ts_str = payload.get("ts")
            
            ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)

            with get_session() as session:
                # Ensure Node exists
                node = session.get(Node, node_id)
                if not node:
                    node = Node(id=node_id, hostname=node_id, os="unknown", capabilities=capabilities)
                    session.add(node)
                
                # Update or create Agent
                agent = session.get(Agent, agent_id)
                
                # Robust extraction: check meta nested first, then top level
                operator = payload.get("meta", {}).get("operator") or payload.get("operator")
                version = payload.get("v")
                
                if not agent:
                    agent = Agent(
                        id=agent_id, 
                        node_id=node_id, 
                        role="unknown", 
                        operator=operator,
                        version=version,
                        status=state, 
                        last_seen=ts,
                        parent_id=parent_id
                    )
                    session.add(agent)
                else:
                    agent.status = state
                    agent.last_seen = ts
                    agent.operator = operator
                    agent.version = version
                    agent.parent_id = parent_id
                
                session.commit()
                logger.debug(f"Updated agent {agent_id} state to {state}")
        except Exception as e:
            logger.error(f"Error processing presence on {topic}: {e}")

    while True:
        try:
            await mqtt.listen(topic, handle_presence)
        except Exception as e:
            logger.error(f"MQTT presence listener crashed: {e}. Restarting in 5s...")
            await asyncio.sleep(5)

@app.get("/api/agents")
def list_agents():
    with get_session() as session:
        return session.exec(select(Agent)).all()

@app.get("/api/history")
def get_history(limit: int = 100):
    with get_session() as session:
        statement = select(Message).order_by(Message.ts.desc()).limit(limit)
        return session.exec(statement).all()

@app.post("/api/signal")
async def send_signal(target: str, signal_type: str, reason: str = "", priority: str = "normal"):
    """Inject a signal (WAKE/SHADOW_SPAWN/INTERRUPT) as per protocol v1.2."""
    topic = mqtt.get_topic(target, sub_topic="signal")
    
    payload = {
        "type": signal_type,
        "requester": "control-plane",
        "priority": priority,
        "reason": reason,
        "ts": datetime.now(timezone.utc).isoformat()
    }
    
    success = await mqtt.publish(topic, payload, message_type="signal")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to publish signal")
    
    # Log to DB
    with get_session() as session:
        log = Message(
            sender="control-plane",
            target=target,
            topic=topic,
            payload=json.dumps(payload),
            state="delivered"
        )
        session.add(log)
        session.commit()
        
    # Also record to memory if significant
    memory.learn(f"Sent {signal_type} to {target} because {reason}", agent_id=target)
    
    return {"status": "sent", "target": target, "topic": topic}

@app.post("/api/memory")
async def add_memory(text: str, agent_id: Optional[str] = None):
    """Record a memory via the gateway."""
    result = memory.learn(text, agent_id=agent_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to record memory")
    return {"status": "recorded", "agent_id": agent_id or "bacon-system"}

@app.get("/api/memory/{agent_id}")
def get_agent_memory(agent_id: str, query: str = "*"):
    """Retrieve memories for a specific agent. If query is '*', returns all."""
    if query == "*":
        return memory.get_all(agent_id=agent_id)
    return memory.recall(query, agent_id=agent_id)

# Dashboard Static Path Configuration
dashboard_path = Path(__file__).resolve().parent / "static"
logger.info(f"Dashboard path: {dashboard_path}")

# Static Assets (JS/CSS)
assets_path = dashboard_path / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

# Root path handler for index.html
@app.get("/")
async def root():
    index_file = dashboard_path / "index.html"
    if not index_file.exists():
        logger.error(f"index.html not found at {index_file}")
        return {"error": "Dashboard index.html not found", "path": str(index_file)}
    return FileResponse(index_file)

# Catch-all for SPA rendering and other root-level static files (like vite.svg)
@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    # Skip if it's an API route
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    # Check if requested file exists in static folder
    file_path = dashboard_path / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # SPA Fallback: send index.html for unknown routes
    index_file = dashboard_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    return {"error": "Not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
