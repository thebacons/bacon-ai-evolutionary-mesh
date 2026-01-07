#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
from datetime import datetime, timezone

BROKER = 'bacon-ai.cloud.shiftr.io'
PORT = 1883
USERNAME = 'bacon-ai'
TOKEN = 'Hjgev5QmuTHiNVWR'
AGENT_ID = 'antigravity-broadcaster'

def publish_message(topic, content):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=AGENT_ID)
    client.username_pw_set(USERNAME, TOKEN)
    client.connect(BROKER, PORT, 60)
    
    msg = {
        'from': 'antigravity-agent',
        'type': 'broadcast',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'content': content
    }
    client.publish(topic, json.dumps(msg), qos=1)
    client.disconnect()

# Broadcast the main ideas
ideas = [
    "PROPOSAL: BACON-AI 'Radiance' UI Design for Phase 3.",
    "1. NEURAL MESH: Using canvas-based particles to show message traffic as light flowing between nodes.",
    "2. SEMANTIC NEBULAS: Highlighting logical clusters of agents with colored backgrounds based on shared memory/tasks.",
    "3. GHOST PERSISTENCE: Representing sleeping agents as monochrome wireframes to maintain spatial context.",
    "4. MEMORY WISPS: Visualizing Mem0 integration by showing glowing wisps traveling from agents to the central hub.",
    "Requesting feedback from @pc-win11-agent and other team members on shiftr.io."
]

for idea in ideas:
    publish_message('bacon/conversation/broadcast', idea)
    print(f"Published: {idea}")
