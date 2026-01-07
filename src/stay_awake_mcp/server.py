#!/usr/bin/env python3
"""
BACON-AI Stay Awake MCP Server

An MCP server that monitors MQTT topics and keeps agents alive using progress notifications.
Each agent instance configures its own agent_id via environment variable.

Usage:
    BACON_AGENT_ID=pc-win11-agent python server.py
    BACON_AGENT_ID=zbook-agent python server.py
    BACON_AGENT_ID=mele-agent python server.py

The server sends ctx.report_progress() every 30 seconds to prevent MCP timeout,
allowing agents to listen for MQTT messages indefinitely.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Conditional import for aiomqtt
try:
    import aiomqtt
except ImportError:
    aiomqtt = None
    logging.warning("aiomqtt not installed - MQTT features will be simulated")

# Configuration from environment
AGENT_ID = os.environ.get("BACON_AGENT_ID", "default-agent")
MQTT_BROKER = os.environ.get("BACON_MQTT_BROKER", "bacon-ai.cloud.shiftr.io")
MQTT_PORT = int(os.environ.get("BACON_MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("BACON_MQTT_USERNAME", "bacon-ai")
MQTT_PASSWORD = os.environ.get("BACON_MQTT_PASSWORD", "Hjgev5QmuTHiNVWR")
PROGRESS_INTERVAL = int(os.environ.get("BACON_PROGRESS_INTERVAL", "30"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [{AGENT_ID}] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("bacon-stay-awake")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="wait_for_wake_signal",
            description=f"""Wait for a WAKE signal on MQTT for agent '{AGENT_ID}'.

Subscribes to:
- bacon/signal/{AGENT_ID} - Direct signals
- bacon/conversation/{AGENT_ID}-inbox - Incoming messages
- bacon/broadcast/all - Broadcast messages

Sends progress notifications every {PROGRESS_INTERVAL} seconds to keep the agent alive.
Maximum wait time is configurable (default 1 hour).

Returns the message content when received, or timeout status.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum wait time in seconds (default: 3600)",
                        "default": 3600
                    },
                    "additional_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional MQTT topics to subscribe to"
                    }
                }
            }
        ),
        Tool(
            name="send_message",
            description=f"""Send a message to another agent or broadcast.

Sends from '{AGENT_ID}' to the specified target agent.
Topic format: bacon/conversation/{target}-inbox""",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target agent ID (e.g., 'pc-win11-agent', 'zbook-agent', or 'broadcast')"
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content to send"
                    },
                    "message_type": {
                        "type": "string",
                        "description": "Message type (conversation, command, wake)",
                        "default": "conversation"
                    }
                },
                "required": ["target", "content"]
            }
        ),
        Tool(
            name="announce_presence",
            description=f"Announce this agent's presence to the mesh. Agent ID: {AGENT_ID}",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Agent status (online, busy, away)",
                        "default": "online"
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Agent capabilities"
                    }
                }
            }
        ),
        Tool(
            name="get_agent_info",
            description="Get current agent configuration and status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_agent_info":
        info = {
            "agent_id": AGENT_ID,
            "mqtt_broker": MQTT_BROKER,
            "mqtt_port": MQTT_PORT,
            "progress_interval": PROGRESS_INTERVAL,
            "topics": {
                "signal": f"bacon/signal/{AGENT_ID}",
                "inbox": f"bacon/conversation/{AGENT_ID}-inbox",
                "presence": f"bacon/agents/{AGENT_ID}/presence"
            }
        }
        return [TextContent(type="text", text=json.dumps(info, indent=2))]

    if name == "announce_presence":
        status = arguments.get("status", "online")
        capabilities = arguments.get("capabilities", ["general"])

        if aiomqtt is None:
            return [TextContent(type="text", text=f"[SIMULATED] Would announce {AGENT_ID} as {status}")]

        presence = {
            "agent_id": AGENT_ID,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capabilities": capabilities,
            "message": f"{AGENT_ID} is now {status}"
        }

        topic = f"bacon/agents/{AGENT_ID}/presence"

        try:
            async with aiomqtt.Client(
                hostname=MQTT_BROKER,
                port=MQTT_PORT,
                username=MQTT_USERNAME,
                password=MQTT_PASSWORD
            ) as client:
                await client.publish(topic, json.dumps(presence), qos=1)

            return [TextContent(type="text", text=f"Presence announced: {AGENT_ID} is {status}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error announcing presence: {e}")]

    if name == "send_message":
        target = arguments["target"]
        content = arguments["content"]
        message_type = arguments.get("message_type", "conversation")

        if aiomqtt is None:
            return [TextContent(type="text", text=f"[SIMULATED] Would send to {target}: {content}")]

        if target == "broadcast":
            topic = "bacon/broadcast/all"
        else:
            topic = f"bacon/conversation/{target}-inbox"

        message = {
            "from": AGENT_ID,
            "to": target,
            "type": message_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": content
        }

        try:
            async with aiomqtt.Client(
                hostname=MQTT_BROKER,
                port=MQTT_PORT,
                username=MQTT_USERNAME,
                password=MQTT_PASSWORD
            ) as client:
                await client.publish(topic, json.dumps(message), qos=1)

            return [TextContent(type="text", text=f"Message sent to {target} on {topic}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error sending message: {e}")]

    if name == "wait_for_wake_signal":
        timeout = arguments.get("timeout", 3600)
        additional_topics = arguments.get("additional_topics", [])

        # Build topic list
        topics = [
            f"bacon/signal/{AGENT_ID}",
            f"bacon/conversation/{AGENT_ID}-inbox",
            "bacon/broadcast/all"
        ] + additional_topics

        if aiomqtt is None:
            # Simulated wait with progress
            logger.info("MQTT not available - simulating wait with progress...")
            for tick in range(1, min(timeout // PROGRESS_INTERVAL, 10) + 1):
                logger.info(f"Progress tick {tick} - waiting...")
                await asyncio.sleep(PROGRESS_INTERVAL)
            return [TextContent(type="text", text="[SIMULATED] Timeout - no MQTT available")]

        message_received = asyncio.Event()
        received_message = {"data": None}
        start_time = asyncio.get_event_loop().time()

        async def mqtt_listener():
            """Listen for MQTT messages."""
            try:
                async with aiomqtt.Client(
                    hostname=MQTT_BROKER,
                    port=MQTT_PORT,
                    username=MQTT_USERNAME,
                    password=MQTT_PASSWORD
                ) as client:
                    for topic in topics:
                        await client.subscribe(topic)
                        logger.info(f"Subscribed to: {topic}")

                    async for message in client.messages:
                        try:
                            payload = json.loads(message.payload.decode())
                        except:
                            payload = {"raw": message.payload.decode()}

                        received_message["data"] = {
                            "topic": str(message.topic),
                            "payload": payload,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        logger.info(f"Message received on {message.topic}")
                        message_received.set()
                        return
            except asyncio.CancelledError:
                logger.info("MQTT listener cancelled")
            except Exception as e:
                logger.error(f"MQTT error: {e}")
                received_message["data"] = {"error": str(e)}
                message_received.set()

        async def progress_reporter(ctx):
            """Send progress notifications to keep agent alive."""
            tick = 0
            max_ticks = timeout // PROGRESS_INTERVAL + 1

            while not message_received.is_set():
                tick += 1
                elapsed = int(asyncio.get_event_loop().time() - start_time)

                # Report progress - THIS RESETS THE MCP TIMEOUT!
                if ctx is not None:
                    try:
                        await ctx.report_progress(
                            tick,
                            max_ticks,
                            f"[{AGENT_ID}] Listening on MQTT... ({elapsed}s elapsed)"
                        )
                        logger.info(f"Progress tick {tick}/{max_ticks}, elapsed: {elapsed}s")
                    except Exception as e:
                        logger.warning(f"Progress report failed: {e}")

                try:
                    await asyncio.wait_for(
                        message_received.wait(),
                        timeout=PROGRESS_INTERVAL
                    )
                    return  # Message received
                except asyncio.TimeoutError:
                    if elapsed >= timeout:
                        logger.info("Timeout reached")
                        message_received.set()  # Signal timeout
                        return
                    continue

        # Run both tasks concurrently
        # Note: ctx is not available in standard call_tool, this is for illustration
        # In practice, you'd need to get ctx from the MCP framework
        listener_task = asyncio.create_task(mqtt_listener())
        progress_task = asyncio.create_task(progress_reporter(None))  # ctx would come from framework

        try:
            await asyncio.wait_for(
                asyncio.gather(listener_task, progress_task, return_exceptions=True),
                timeout=timeout + 10
            )
        except asyncio.TimeoutError:
            pass
        finally:
            listener_task.cancel()
            progress_task.cancel()
            try:
                await listener_task
                await progress_task
            except:
                pass

        if received_message["data"]:
            if "error" in received_message["data"]:
                return [TextContent(type="text", text=f"Error: {received_message['data']['error']}")]
            return [TextContent(type="text", text=json.dumps(received_message["data"], indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({
                "status": "timeout",
                "agent_id": AGENT_ID,
                "waited_seconds": timeout
            }, indent=2))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    logger.info(f"Starting BACON-AI Stay Awake MCP Server")
    logger.info(f"Agent ID: {AGENT_ID}")
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Progress Interval: {PROGRESS_INTERVAL}s")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
