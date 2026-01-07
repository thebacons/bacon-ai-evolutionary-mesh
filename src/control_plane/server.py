"""
BACON MQTT MCP Server - Cross-Machine Claude Wake System (v2.0)

Refactored to use modular components from the BACON-AI Control Plane.
"""

import os
import asyncio
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mqtt_handler import MQTTHandler
from memory_gateway import MemoryGateway

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bacon-mqtt-mcp")

# MQTT Configuration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "srv906866.hstgr.cloud")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")

# Initialize modular components
mqtt = MQTTHandler(MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS)
memory = MemoryGateway()

# Initialize MCP server
mcp = FastMCP(
    name="bacon-mqtt",
    instructions="Cross-machine Claude wake system using MQTT v1.2",
)

@mcp.tool()
async def wait_for_message(
    topic: Optional[str] = None,
    timeout: int = 3600,
    session_id: Optional[str] = None,
    ctx=None
) -> dict:
    """
    Block until a message arrives on the specified MQTT topic.
    
    This tool is designed to be called by a background sub-agent to enable
    cross-machine wake functionality. It sends progress notifications every
    30 seconds to keep the MCP connection alive.
    """
    target_topic = topic or mqtt.get_topic(session_id)
    logger.info(f"Starting wait_for_message on topic: {target_topic}")
    
    async def on_progress(tick, max_ticks, message):
        if ctx:
            await ctx.report_progress(tick, max_ticks, message)
            
    return await mqtt.wait_for_message(target_topic, timeout=timeout, on_progress=on_progress)

@mcp.tool()
async def send_message(
    message: str,
    target_session: Optional[str] = None,
    topic: Optional[str] = None,
    message_type: str = "text",
) -> dict:
    """Send a message to another Claude session via MQTT."""
    target_topic = topic or mqtt.get_topic(target_session)
    success = await mqtt.publish(target_topic, message, message_type=message_type)
    
    return {
        "status": "sent" if success else "error",
        "topic": target_topic
    }

@mcp.tool()
async def learn_memory(text: str, agent_id: Optional[str] = None):
    """Save a semantic memory for the system or a specific agent."""
    result = memory.learn(text, agent_id=agent_id)
    return {"status": "success" if result else "error"}

@mcp.tool()
async def recall_memory(query: str, agent_id: Optional[str] = None):
    """Retrieve relevant memories based on a query."""
    results = memory.recall(query, agent_id=agent_id)
    return {"memories": results}

@mcp.tool()
async def get_status() -> dict:
    """Get the current status of the MQTT connection and server."""
    return {
        "server": "bacon-mqtt-mcp",
        "version": "2.0.0",
        "hostname": mqtt.hostname,
        "mqtt_broker": mqtt.broker,
        "mqtt_port": mqtt.port,
        "default_topic": mqtt.get_topic(),
    }

if __name__ == "__main__":
    mcp.run()
