import asyncio
import json
import logging
import socket
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any, Union
import aiomqtt

logger = logging.getLogger("bacon-mqtt-handler")

class MQTTHandler:
    def __init__(self, broker: str, port: int = 1883, username: str = "", password: str = ""):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.hostname = socket.gethostname().lower().replace(".", "-")
        self._connect_kwargs = {
            "hostname": self.broker,
            "port": self.port,
        }
        if self.username:
            self._connect_kwargs["username"] = self.username
        if self.password:
            self._connect_kwargs["password"] = self.password

    def get_topic(self, session_id: Optional[str] = None, sub_topic: str = "data") -> str:
        """Construct MQTT topic for a session using v1 namespace."""
        target = session_id or self.hostname
        if sub_topic == "presence":
            return f"bacon/v1/presence/agent/{target}"
        return f"bacon/v1/{sub_topic}/{target}"

    async def publish(self, topic: str, message: Union[str, Dict], message_type: str = "text"):
        """Publish a message to a topic."""
        envelope = {
            "type": message_type,
            "content": message,
            "source": self.hostname,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            async with aiomqtt.Client(**self._connect_kwargs) as client:
                await client.publish(
                    topic,
                    json.dumps(envelope),
                    qos=1
                )
                logger.info(f"Published message to {topic}")
                return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False

    async def wait_for_message(self, topic: str, timeout: int = 3600, on_progress: Optional[Callable[[int, int, str], None]] = None):
        """Block until a message is received on a topic."""
        start_time = asyncio.get_event_loop().time()
        message_received = asyncio.Event()
        received_data = {"payload": None, "topic": None}

        async def mqtt_listener():
            try:
                async with aiomqtt.Client(**self._connect_kwargs) as client:
                    await client.subscribe(topic)
                    async for msg in client.messages:
                        payload = msg.payload.decode('utf-8')
                        try:
                            received_data["payload"] = json.loads(payload)
                        except json.JSONDecodeError:
                            received_data["payload"] = payload
                        received_data["topic"] = str(msg.topic)
                        message_received.set()
                        return
            except Exception as e:
                logger.error(f"MQTT listener error: {e}")
                received_data["payload"] = f"MQTT error: {str(e)}"
                message_received.set()

        async def reporter():
            if not on_progress:
                return
            tick = 0
            max_ticks = timeout // 30 + 1
            while not message_received.is_set():
                tick += 1
                elapsed = int(asyncio.get_event_loop().time() - start_time)
                await on_progress(tick, max_ticks, f"Listening on {topic}... ({elapsed}s elapsed)")
                try:
                    await asyncio.wait_for(message_received.wait(), timeout=30)
                    return
                except asyncio.TimeoutError:
                    continue

        listener_task = asyncio.create_task(mqtt_listener())
        reporter_task = asyncio.create_task(reporter())

        try:
            await asyncio.wait_for(message_received.wait(), timeout=timeout)
            return {
                "status": "received",
                "message": received_data["payload"],
                "topic": received_data["topic"] or topic,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "message": None,
                "topic": topic,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        finally:
            listener_task.cancel()
            reporter_task.cancel()
            try:
                await asyncio.gather(listener_task, reporter_task, return_exceptions=True)
            except Exception:
                pass

    async def listen(self, topic: str, callback: Callable[[str, Dict], None]):
        """Subscribe to a topic and execute callback for each message."""
        try:
            async with aiomqtt.Client(**self._connect_kwargs) as client:
                await client.subscribe(topic)
                logger.info(f"Persistent listener subscribed to {topic}")
                async for msg in client.messages:
                    payload = msg.payload.decode('utf-8')
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        data = payload
                    
                    if asyncio.iscoroutinefunction(callback):
                        await callback(str(msg.topic), data)
                    else:
                        callback(str(msg.topic), data)
        except Exception as e:
            logger.error(f"Persistent listener error on {topic}: {e}")
            await asyncio.sleep(5)  # Backoff before retry
