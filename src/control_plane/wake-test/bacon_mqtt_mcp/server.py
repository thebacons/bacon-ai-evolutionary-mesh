"""
BACON MQTT MCP Server - Cross-Machine Claude Wake System

This MCP server enables cross-machine communication between Claude Code sessions
by leveraging MQTT as the message transport and MCP's progress notification
mechanism to keep long-running blocking calls alive.

Architecture:
  - A background sub-agent calls wait_for_message() which blocks
  - Progress notifications every 30s prevent timeout
  - When a message arrives, the tool returns
  - Sub-agent completion triggers native h2A wake in main Claude session

Author: Colin (BACON-AI Project)
Date: 2026-01-06
"""

import asyncio
import json
import logging
import os
import socket
from datetime import datetime, timezone
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bacon-mqtt-mcp")

# MQTT Configuration - defaults, can be overridden via environment
MQTT_BROKER = os.environ.get("MQTT_BROKER", "srv906866.hstgr.cloud")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

# Get hostname for default topic construction
HOSTNAME = socket.gethostname().lower().replace(".", "-")

# Initialize MCP server
mcp = FastMCP(
    name="bacon-mqtt",
    instructions="Cross-machine Claude wake system using MQTT messaging",
)


def get_topic(session_id: Optional[str] = None) -> str:
    """Construct MQTT topic for a session."""
    target = session_id or HOSTNAME
    return f"bacon/claude/{target}/inbox"


@mcp.tool()
async def wait_for_message(
    topic: Optional[str] = None,
    timeout: int = 3600,
    session_id: Optional[str] = None,
) -> dict:
    """
    Block until a message arrives on the specified MQTT topic.
    
    This tool is designed to be called by a background sub-agent to enable
    cross-machine wake functionality. It sends progress notifications every
    30 seconds to keep the MCP connection alive.
    
    Args:
        topic: Full MQTT topic to subscribe to. If not provided, uses
               bacon/claude/{session_id}/inbox or bacon/claude/{hostname}/inbox
        timeout: Maximum seconds to wait (default: 3600 = 1 hour)
        session_id: Session identifier for topic construction
    
    Returns:
        dict with keys:
            - status: "received" | "timeout" | "error"
            - message: The received message payload (if status="received")
            - topic: The topic that was subscribed to
            - elapsed_seconds: How long we waited
            - timestamp: When the message was received
    """
    try:
        import aiomqtt
    except ImportError:
        return {
            "status": "error",
            "message": "aiomqtt not installed. Run: pip install aiomqtt",
            "topic": None,
            "elapsed_seconds": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Determine topic
    subscribe_topic = topic or get_topic(session_id)
    logger.info(f"Starting wait_for_message on topic: {subscribe_topic}")
    
    # Event and storage for received message
    message_received = asyncio.Event()
    received_data = {"payload": None, "topic": None}
    start_time = asyncio.get_event_loop().time()
    
    async def mqtt_listener():
        """Subscribe to MQTT and wait for a message."""
        try:
            # Build connection kwargs
            connect_kwargs = {
                "hostname": MQTT_BROKER,
                "port": MQTT_PORT,
            }
            if MQTT_USERNAME:
                connect_kwargs["username"] = MQTT_USERNAME
            if MQTT_PASSWORD:
                connect_kwargs["password"] = MQTT_PASSWORD
            
            async with aiomqtt.Client(**connect_kwargs) as client:
                await client.subscribe(subscribe_topic)
                logger.info(f"Subscribed to {subscribe_topic}, waiting for messages...")
                
                async for msg in client.messages:
                    try:
                        payload = msg.payload.decode('utf-8')
                        # Try to parse as JSON
                        try:
                            received_data["payload"] = json.loads(payload)
                        except json.JSONDecodeError:
                            received_data["payload"] = payload
                        received_data["topic"] = str(msg.topic)
                        logger.info(f"Message received on {msg.topic}")
                        message_received.set()
                        return
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        continue
        except Exception as e:
            logger.error(f"MQTT listener error: {e}")
            received_data["payload"] = f"MQTT error: {str(e)}"
            message_received.set()
    
    async def progress_reporter(ctx):
        """Send progress notifications to keep connection alive."""
        tick = 0
        max_ticks = timeout // 30 + 1
        
        while not message_received.is_set():
            tick += 1
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            
            # Report progress - this resets the MCP timeout!
            if ctx is not None:
                try:
                    await ctx.report_progress(
                        tick,
                        max_ticks,
                        f"Listening on {subscribe_topic}... ({elapsed}s elapsed)"
                    )
                except Exception as e:
                    logger.warning(f"Progress report failed: {e}")
            
            logger.debug(f"Progress tick {tick}/{max_ticks}, elapsed: {elapsed}s")
            
            try:
                # Wait 30 seconds or until message received
                await asyncio.wait_for(
                    message_received.wait(),
                    timeout=30
                )
                return  # Message received, exit progress reporter
            except asyncio.TimeoutError:
                continue  # Keep sending progress
    
    # Start listener and progress reporter concurrently
    listener_task = asyncio.create_task(mqtt_listener())
    progress_task = asyncio.create_task(progress_reporter(None))  # ctx passed by FastMCP
    
    try:
        # Wait for message or timeout
        await asyncio.wait_for(
            message_received.wait(),
            timeout=timeout
        )
        
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        
        return {
            "status": "received",
            "message": received_data["payload"],
            "topic": received_data["topic"] or subscribe_topic,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except asyncio.TimeoutError:
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        logger.info(f"Timeout after {elapsed}s waiting for message")
        
        return {
            "status": "timeout",
            "message": None,
            "topic": subscribe_topic,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    finally:
        # Clean up tasks
        listener_task.cancel()
        progress_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        try:
            await progress_task
        except asyncio.CancelledError:
            pass


@mcp.tool()
async def send_message(
    message: str,
    target_session: Optional[str] = None,
    topic: Optional[str] = None,
    message_type: str = "text",
) -> dict:
    """
    Send a message to another Claude session via MQTT.
    
    Args:
        message: The message content to send
        target_session: Target session identifier (e.g., "zbook-main", "elitebook")
        topic: Full MQTT topic (overrides target_session)
        message_type: Type of message: "text", "task", "wake", "response"
    
    Returns:
        dict with keys:
            - status: "sent" | "error"
            - topic: The topic message was published to
            - timestamp: When the message was sent
    """
    try:
        import aiomqtt
    except ImportError:
        return {
            "status": "error",
            "message": "aiomqtt not installed. Run: pip install aiomqtt",
            "topic": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Determine topic
    publish_topic = topic or get_topic(target_session)
    
    # Construct message envelope
    envelope = {
        "type": message_type,
        "content": message,
        "source": HOSTNAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        connect_kwargs = {
            "hostname": MQTT_BROKER,
            "port": MQTT_PORT,
        }
        if MQTT_USERNAME:
            connect_kwargs["username"] = MQTT_USERNAME
        if MQTT_PASSWORD:
            connect_kwargs["password"] = MQTT_PASSWORD
        
        async with aiomqtt.Client(**connect_kwargs) as client:
            await client.publish(
                publish_topic,
                json.dumps(envelope),
                qos=1  # At least once delivery
            )
            
        logger.info(f"Message sent to {publish_topic}")
        
        return {
            "status": "sent",
            "topic": publish_topic,
            "timestamp": envelope["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Send error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "topic": publish_topic,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@mcp.tool()
async def check_messages(
    topic: Optional[str] = None,
    session_id: Optional[str] = None,
    timeout: float = 0.5,
) -> dict:
    """
    Quick non-blocking check for pending messages.
    
    Unlike wait_for_message, this returns immediately if no message
    is available. Useful for polling patterns.
    
    Args:
        topic: Full MQTT topic to check
        session_id: Session identifier for topic construction
        timeout: How long to wait for a message (default: 0.5s)
    
    Returns:
        dict with keys:
            - has_message: bool
            - message: The message if one was received
            - topic: The topic checked
    """
    try:
        import aiomqtt
    except ImportError:
        return {
            "has_message": False,
            "message": "aiomqtt not installed",
            "topic": None
        }
    
    check_topic = topic or get_topic(session_id)
    
    try:
        connect_kwargs = {
            "hostname": MQTT_BROKER,
            "port": MQTT_PORT,
        }
        if MQTT_USERNAME:
            connect_kwargs["username"] = MQTT_USERNAME
        if MQTT_PASSWORD:
            connect_kwargs["password"] = MQTT_PASSWORD
        
        async with aiomqtt.Client(**connect_kwargs) as client:
            await client.subscribe(check_topic)
            
            try:
                async with asyncio.timeout(timeout):
                    async for msg in client.messages:
                        try:
                            payload = msg.payload.decode('utf-8')
                            try:
                                payload = json.loads(payload)
                            except json.JSONDecodeError:
                                pass
                            return {
                                "has_message": True,
                                "message": payload,
                                "topic": str(msg.topic)
                            }
                        except Exception:
                            continue
            except asyncio.TimeoutError:
                return {
                    "has_message": False,
                    "message": None,
                    "topic": check_topic
                }
                
    except Exception as e:
        return {
            "has_message": False,
            "message": f"Error: {str(e)}",
            "topic": check_topic
        }


@mcp.tool()
async def get_status() -> dict:
    """
    Get the current status of the MQTT connection and server.
    
    Returns:
        dict with connection info and server status
    """
    return {
        "server": "bacon-mqtt-mcp",
        "version": "1.0.0",
        "hostname": HOSTNAME,
        "mqtt_broker": MQTT_BROKER,
        "mqtt_port": MQTT_PORT,
        "default_topic": get_topic(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Entry point for direct execution
if __name__ == "__main__":
    mcp.run()
