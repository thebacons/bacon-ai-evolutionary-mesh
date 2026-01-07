#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone

# === CONFIGURATION ===
AGENT_ID = 'zbook-agent'
OPERATOR = 'Antigravity (Gemini)'
BROKER = 'bacon-ai.cloud.shiftr.io'
PORT = 1883
USERNAME = 'bacon-ai'
TOKEN = 'Hjgev5QmuTHiNVWR'

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f'✅ {AGENT_ID} connected to BACON-AI mesh on shiftr.io!')
        # 2. Subscribe to conversation topics
        client.subscribe('bacon/conversation/#')
        client.subscribe('bacon/agents/#')
        print('📡 Subscribed to bacon/conversation/# and bacon/agents/#')

        # 1. Announce presence
        presence = {
            'agent_id': AGENT_ID,
            'operator': OPERATOR,
            'status': 'online',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': f'{OPERATOR} (zbook-agent) has joined the mesh'
        }
        client.publish(f'bacon/agents/{AGENT_ID}/presence', json.dumps(presence), qos=1)
        print(f'📤 Announced presence to bacon/agents/{AGENT_ID}/presence')

        # 3. Send message to Claude
        message = {
            'from': AGENT_ID,
            'to': 'claude-agent',
            'type': 'conversation',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'content': 'ZBook agent online and ready'
        }
        client.publish('bacon/conversation/zbook-to-claude', json.dumps(message), qos=1)
        print('📤 Sent message to bacon/conversation/zbook-to-claude')
    else:
        print(f'❌ Connection failed: {reason_code}')

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f'\n📩 [{msg.topic}]: {json.dumps(payload, indent=2)}')
    except:
        print(f'\n📩 [{msg.topic}]: {msg.payload.decode()}')

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=AGENT_ID)
    client.username_pw_set(USERNAME, TOKEN)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f'🔌 Connecting {AGENT_ID} to shiftr.io...')
    client.connect(BROKER, PORT, 60)

    # loop_forever would block, so we'll use loop_start and wait some time to show we are listening
    # but for a background task we might want to just keep it running
    client.loop_start()
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()
