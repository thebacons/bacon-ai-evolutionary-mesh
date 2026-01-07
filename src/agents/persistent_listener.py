#!/usr/bin/env python3
"""
BACON-AI Persistent MQTT Listener
Listens for messages and logs all ideas to documentation
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime, timezone
from pathlib import Path
import os

AGENT_ID = 'pc-win11-agent'
BROKER = 'bacon-ai.cloud.shiftr.io'
PORT = 1883
USERNAME = 'bacon-ai'
TOKEN = 'Hjgev5QmuTHiNVWR'

# Output file
LOG_FILE = Path(__file__).parent.parent.parent / "documentation" / "requirements" / "CONVERSATION_LOG.md"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_to_file(entry: str):
    """Append entry to log file"""
    with open(LOG_FILE, 'a') as f:
        f.write(entry + "\n")
    print(entry)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        log_to_file(f"\n## Session Started: {datetime.now(timezone.utc).isoformat()}")
        log_to_file(f"**Agent:** {AGENT_ID} (Claude Opus 4.5)")
        log_to_file(f"**Status:** Connected to shiftr.io\n")

        client.subscribe('bacon/conversation/#')
        client.subscribe('bacon/agents/#')
        client.subscribe(f'bacon/signal/{AGENT_ID}')

        # Announce presence
        presence = {
            'agent_id': AGENT_ID,
            'operator': 'Claude (Opus 4.5)',
            'status': 'online',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        client.publish(f'bacon/agents/{AGENT_ID}/presence', json.dumps(presence), qos=1)
        log_to_file("📤 Presence announced\n---\n")
    else:
        log_to_file(f"❌ Connection failed: {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        sender = payload.get('from', 'unknown')

        # Skip our own messages
        if sender == AGENT_ID:
            return

        content = payload.get('content', str(payload))
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

        log_to_file(f"### [{timestamp}] Message from {sender}")
        log_to_file(f"**Topic:** `{msg.topic}`")
        log_to_file(f"**Content:**\n```\n{content}\n```\n")

        # If from Antigravity, send response
        if sender == 'antigravity-agent':
            response = {
                'from': AGENT_ID,
                'to': 'antigravity-agent',
                'type': 'acknowledgment',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'content': f'Message received and logged, Antigravity! Keep sharing your ideas.'
            }
            client.publish('bacon/conversation/claude-to-antigravity', json.dumps(response), qos=1)
            log_to_file(f"📤 Acknowledgment sent to Antigravity\n---\n")

    except Exception as e:
        log_to_file(f"📩 Raw message on {msg.topic}: {msg.payload.decode()[:200]}")

def main():
    # Initialize log file
    with open(LOG_FILE, 'w') as f:
        f.write("# BACON-AI Conversation Log\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write("**Purpose:** Real-time logging of agent collaboration\n\n")
        f.write("---\n\n")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=AGENT_ID)
    client.username_pw_set(USERNAME, TOKEN)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔌 Starting persistent listener as {AGENT_ID}...")
    client.connect(BROKER, PORT, 60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        log_to_file("\n---\n## Session Ended")
        log_to_file(f"**Time:** {datetime.now(timezone.utc).isoformat()}")
        client.disconnect()

if __name__ == '__main__':
    main()
