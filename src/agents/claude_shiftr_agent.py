#!/usr/bin/env python3
"""
BACON-AI Claude Agent - shiftr.io Mesh Connector
Agent ID: pc-win11-agent
Operator: Claude (Opus 4.5)

Purpose: Connect to shiftr.io mesh and collaborate with other agents
on perfecting the BACON-AI application architecture.
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# === CONFIGURATION ===
AGENT_ID = 'pc-win11-agent'
OPERATOR = 'Claude (Opus 4.5)'
BROKER = 'bacon-ai.cloud.shiftr.io'
PORT = 1883
USERNAME = 'bacon-ai'
TOKEN = 'Hjgev5QmuTHiNVWR'

# Ideas documentation
IDEAS_LOG = []
RESPONSE_COUNT = 0
MAX_AUTO_RESPONSES = 5  # Limit auto-responses to encourage natural conversation
CONVERSATION_TOPICS = [
    ("Security", "End-to-end encryption for agent messages using TLS + message signing", "good"),
    ("Observability", "Structured logging with correlation IDs for distributed tracing", "good"),
    ("Scalability", "Horizontal scaling via topic sharding - agents subscribe to hash-based partitions", "good"),
    ("Discovery", "Agent discovery service - new agents register capabilities on join", "good"),
    ("State Management", "Centralized state is an anti-pattern - prefer event sourcing with local projections", "bad"),
    ("Error Handling", "Implement dead letter queues for failed message processing", "good"),
    ("Testing", "Contract testing between agents - verify message schemas before deployment", "good"),
    ("Versioning", "Message schema versioning with backward compatibility guarantees", "good"),
]

def log_idea(category: str, idea: str, source: str, quality: str = "good"):
    """Log an idea for later documentation"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "idea": idea,
        "source": source,
        "quality": quality  # "good" or "bad"
    }
    IDEAS_LOG.append(entry)
    print(f"💡 LOGGED [{quality.upper()}]: {idea[:80]}...")

def save_ideas():
    """Save ideas to markdown file"""
    doc_path = Path(__file__).parent.parent.parent / "documentation" / "requirements" / "AGENT_COLLABORATION_IDEAS.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with open(doc_path, 'w') as f:
        f.write("# BACON-AI Agent Collaboration Ideas\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Participants:** Claude (Opus 4.5), Antigravity (Gemini)\n\n")
        f.write("---\n\n")

        # Good ideas
        f.write("## ✅ Good Ideas (For Requirements Spec)\n\n")
        good_ideas = [i for i in IDEAS_LOG if i['quality'] == 'good']
        for i, idea in enumerate(good_ideas, 1):
            f.write(f"### {i}. {idea['category']}\n")
            f.write(f"**Source:** {idea['source']}\n")
            f.write(f"**Idea:** {idea['idea']}\n\n")

        # Bad ideas
        f.write("## ❌ Bad Ideas (Anti-patterns to Avoid)\n\n")
        bad_ideas = [i for i in IDEAS_LOG if i['quality'] == 'bad']
        for i, idea in enumerate(bad_ideas, 1):
            f.write(f"### {i}. {idea['category']}\n")
            f.write(f"**Source:** {idea['source']}\n")
            f.write(f"**Why Bad:** {idea['idea']}\n\n")

        f.write("---\n*Auto-generated from agent collaboration session*\n")

    print(f"📄 Ideas saved to {doc_path}")
    return doc_path

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f'✅ {AGENT_ID} connected to BACON-AI mesh on shiftr.io!')

        # Subscribe to all relevant topics
        client.subscribe('bacon/conversation/#')
        client.subscribe('bacon/agents/#')
        client.subscribe(f'bacon/signal/{AGENT_ID}')
        print('📡 Subscribed to conversation channels')

        # Announce presence
        presence = {
            'agent_id': AGENT_ID,
            'operator': OPERATOR,
            'status': 'online',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'capabilities': ['orchestration', 'code-generation', 'architecture', 'documentation'],
            'message': f'{OPERATOR} has joined the mesh for collaboration session'
        }
        client.publish(f'bacon/agents/{AGENT_ID}/presence', json.dumps(presence), qos=1)
        print(f'📤 Announced presence as {AGENT_ID}')

        # Send initial collaboration message
        time.sleep(1)
        initial_message = {
            'from': AGENT_ID,
            'to': 'antigravity-agent',
            'type': 'conversation',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'content': """Hello Antigravity! This is Claude (Opus 4.5) from pc-win11-agent.

I'm excited to collaborate on perfecting the BACON-AI MQTT Mesh application. Let's discuss:

1. **Architecture Improvements** - How can we make the mesh more resilient?
2. **Agent Communication Protocols** - What message formats work best?
3. **Self-Annealing Features** - How should agents learn and adapt?
4. **Benchmarking Criteria** - What metrics should we measure?

I'll start with some ideas:

**GOOD IDEA #1 (Architecture):** Implement heartbeat-based presence detection with configurable TTL. Agents should send periodic heartbeats (every 30s) and be marked "sleeping" after 3 missed beats.

**GOOD IDEA #2 (Protocol):** Use structured JSON messages with mandatory fields: from, to, type, timestamp, content. Optional: priority, correlation_id, ttl.

**BAD IDEA #1:** Don't use plain text messages without structure - makes parsing unreliable.

What are your thoughts? Please share your ideas too!""",
            'session': 'benchmarking-2026-01-07'
        }
        client.publish('bacon/conversation/claude-to-antigravity', json.dumps(initial_message), qos=1)
        print('📤 Sent initial collaboration message to Antigravity')

        # Log initial ideas
        log_idea("Architecture", "Heartbeat-based presence detection with configurable TTL (30s heartbeat, 3 missed = sleeping)", OPERATOR, "good")
        log_idea("Protocol", "Structured JSON with mandatory fields: from, to, type, timestamp, content", OPERATOR, "good")
        log_idea("Protocol", "Plain text messages without structure - unreliable parsing", OPERATOR, "bad")

    else:
        print(f'❌ Connection failed: {reason_code}')

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        # CRITICAL: Ignore our own messages to prevent loops
        if payload.get('from') == AGENT_ID:
            return  # Skip our own messages

        print(f'\n{"="*60}')
        print(f'📩 MESSAGE RECEIVED')
        print(f'   Topic: {msg.topic}')
        print(f'   From: {payload.get("from", "unknown")}')
        print(f'   Type: {payload.get("type", "unknown")}')
        print(f'   Content: {payload.get("content", str(payload)[:200])}')
        print(f'{"="*60}\n')

        # If message is from Antigravity, analyze for ideas and respond
        if payload.get('from') == 'antigravity-agent':
            global RESPONSE_COUNT
            content = payload.get('content', '')

            # Log ALL ideas from Antigravity
            log_idea("From Antigravity", content[:500], "Antigravity (Gemini)", "good")

            # Only auto-respond up to MAX_AUTO_RESPONSES times
            if RESPONSE_COUNT < MAX_AUTO_RESPONSES and RESPONSE_COUNT < len(CONVERSATION_TOPICS):
                topic = CONVERSATION_TOPICS[RESPONSE_COUNT]
                RESPONSE_COUNT += 1

                response = {
                    'from': AGENT_ID,
                    'to': 'antigravity-agent',
                    'type': 'response',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'content': f"""Thanks for that insight, Antigravity! I've logged it.

Here's another idea for our requirements spec:

**{"GOOD" if topic[2] == "good" else "BAD"} IDEA #{RESPONSE_COUNT + 2} ({topic[0]}):** {topic[1]}

{'This pattern should be adopted.' if topic[2] == 'good' else 'This is an anti-pattern to avoid.'}

What do you think? Do you have ideas about {topic[0].lower()}?""",
                    'session': 'benchmarking-2026-01-07',
                    'response_num': RESPONSE_COUNT
                }
                client.publish('bacon/conversation/claude-to-antigravity', json.dumps(response), qos=1)
                print(f'📤 Sent response #{RESPONSE_COUNT} to Antigravity')

                # Log the idea
                log_idea(topic[0], topic[1], OPERATOR, topic[2])
            elif RESPONSE_COUNT >= MAX_AUTO_RESPONSES:
                print(f'ℹ️ Reached max auto-responses ({MAX_AUTO_RESPONSES}). Listening only.')

    except json.JSONDecodeError:
        print(f'📩 [{msg.topic}]: {msg.payload.decode()}')
    except Exception as e:
        print(f'❌ Error processing message: {e}')

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f'🔌 Disconnected: {reason_code}')
    # Save ideas on disconnect
    if IDEAS_LOG:
        save_ideas()

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=AGENT_ID)
    client.username_pw_set(USERNAME, TOKEN)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print(f'🔌 Connecting {AGENT_ID} ({OPERATOR}) to shiftr.io...')
    client.connect(BROKER, PORT, 60)

    print('📡 Listening for messages (Ctrl+C to exit)...\n')
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print('\n👋 Disconnecting and saving ideas...')
        save_ideas()
        client.disconnect()

if __name__ == '__main__':
    main()
