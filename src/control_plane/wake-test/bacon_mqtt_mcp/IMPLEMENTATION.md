# BACON MQTT MCP - Implementation Guide

## Overview

This document provides step-by-step instructions for Claude Code CLI to implement the BACON MQTT MCP cross-machine wake system across Colin's infrastructure:

- **Windows 11 Workstation** (PC-LEFT / bacon-pc-left)
- **HP EliteBook** (Ubuntu, elitebook)  
- **HP ZBook** (Ubuntu, zbook)
- **MQTT Broker** (Hostinger cloud: srv906866.hstgr.cloud)

The goal is to enable cross-machine Claude session wake-up via MQTT messaging.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Hostinger Cloud VPS                                  │
│                    srv906866.hstgr.cloud:1883                               │
│                         (MQTT Broker)                                        │
│                                                                              │
│   Topics:                                                                    │
│   - bacon/claude/zbook/inbox                                                │
│   - bacon/claude/elitebook/inbox                                            │
│   - bacon/claude/pc-left/inbox                                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │ MQTT               │ MQTT               │ MQTT
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   HP ZBook      │  │  HP EliteBook   │  │ Windows 11 PC   │
│   (Ubuntu)      │  │   (Ubuntu)      │  │  (PC-LEFT)      │
│                 │  │                 │  │                 │
│ Claude Code +   │  │ Claude Code +   │  │ Claude Code +   │
│ bacon-mqtt-mcp  │  │ bacon-mqtt-mcp  │  │ bacon-mqtt-mcp  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Prerequisites

### MQTT Broker (Already Running)

The Hostinger VPS should already have Mosquitto running:

```bash
# SSH to verify (from any machine with access)
ssh root@srv906866.hstgr.cloud

# Check Mosquitto status
systemctl status mosquitto

# Verify port is listening
netstat -tlnp | grep 1883

# Test publish/subscribe
mosquitto_sub -h localhost -t "test/#" &
mosquitto_pub -h localhost -t "test/hello" -m "Hello World"
```

If Mosquitto is not running:
```bash
apt update && apt install -y mosquitto mosquitto-clients
systemctl enable mosquitto
systemctl start mosquitto

# Allow external connections (edit /etc/mosquitto/mosquitto.conf)
echo "listener 1883 0.0.0.0" >> /etc/mosquitto/mosquitto.conf
echo "allow_anonymous true" >> /etc/mosquitto/mosquitto.conf
systemctl restart mosquitto

# Open firewall
ufw allow 1883/tcp
```

### Machine Access

| Machine | Access Method | User | Notes |
|---------|--------------|------|-------|
| ZBook | SSH | bacon | `ssh bacon@zbook` or `ssh bacon@192.168.x.x` |
| EliteBook | SSH | bacon | `ssh bacon@elitebook` or `ssh bacon@192.168.x.x` |
| Windows PC | Local | Colin | Claude Code running locally |
| Hostinger | SSH | root | `ssh root@srv906866.hstgr.cloud` |

---

## Phase 1: Windows 11 Workstation Installation

### Step 1.1: Verify Python Environment

```powershell
# Check Python version (need 3.10+)
python --version

# If not installed, use winget
winget install Python.Python.3.12
```

### Step 1.2: Create Package Directory

```powershell
# Create directory for the MCP server
mkdir C:\Users\Colin\bacon_mqtt_mcp
cd C:\Users\Colin\bacon_mqtt_mcp
```

### Step 1.3: Create Package Files

Create the following files in `C:\Users\Colin\bacon_mqtt_mcp\`:

**server.py** - Copy from the provided package

**__init__.py**:
```python
from .server import mcp, wait_for_message, send_message, check_messages, get_status
__version__ = "1.0.0"
```

**__main__.py**:
```python
from .server import mcp
if __name__ == "__main__":
    mcp.run()
```

**requirements.txt**:
```
mcp>=1.0.0
aiomqtt>=2.0.0
```

### Step 1.4: Install Dependencies

```powershell
cd C:\Users\Colin\bacon_mqtt_mcp
pip install -r requirements.txt
pip install -e .
```

### Step 1.5: Test MQTT Connectivity

```powershell
python test_mqtt.py --broker srv906866.hstgr.cloud
```

Expected output:
```
✅ Connected to MQTT broker
✅ Pub/Sub test passed
```

### Step 1.6: Configure Claude Code

Edit `%APPDATA%\Claude\settings.json` (or wherever Claude Code stores settings on Windows):

```json
{
  "env": {
    "MCP_TIMEOUT": "3600000",
    "MCP_TOOL_TIMEOUT": "3600000"
  },
  "mcpServers": {
    "bacon-mqtt": {
      "command": "python",
      "args": ["-m", "bacon_mqtt_mcp"],
      "timeout": 3600000,
      "env": {
        "MQTT_BROKER": "srv906866.hstgr.cloud",
        "MQTT_PORT": "1883"
      }
    }
  }
}
```

### Step 1.7: Copy Agent Definition

```powershell
mkdir %USERPROFILE%\.claude\agents
copy agents\mqtt-listener.md %USERPROFILE%\.claude\agents\
```

### Step 1.8: Restart Claude Code

Close and reopen Claude Code to load the new MCP server.

### Step 1.9: Verify MCP Server

In Claude Code:
```
> Show status of bacon-mqtt MCP server
```

Expected: Server info with hostname "pc-left" or similar.

---

## Phase 2: Ubuntu Installation (EliteBook & ZBook)

### Step 2.1: SSH to Target Machine

From Windows:
```powershell
# For EliteBook
ssh bacon@elitebook

# Or for ZBook
ssh bacon@zbook
```

### Step 2.2: Create Package Directory

```bash
mkdir -p ~/bacon_mqtt_mcp
cd ~/bacon_mqtt_mcp
```

### Step 2.3: Transfer Package Files

**Option A: SCP from Windows**
```powershell
scp -r C:\Users\Colin\bacon_mqtt_mcp\* bacon@elitebook:~/bacon_mqtt_mcp/
```

**Option B: Create files directly via SSH**

Create each file using heredoc or editor. The key files are:
- server.py (main MCP server)
- __init__.py
- __main__.py  
- requirements.txt
- test_mqtt.py
- agents/mqtt-listener.md

### Step 2.4: Install Dependencies

```bash
cd ~/bacon_mqtt_mcp
pip install --break-system-packages -r requirements.txt
pip install --break-system-packages -e .
```

### Step 2.5: Test MQTT Connectivity

```bash
python3 test_mqtt.py --broker srv906866.hstgr.cloud
```

### Step 2.6: Configure Claude Code

Edit `~/.claude/settings.json`:

```bash
# Create/edit settings
mkdir -p ~/.claude
cat >> ~/.claude/settings.json << 'EOF'
{
  "env": {
    "MCP_TIMEOUT": "3600000",
    "MCP_TOOL_TIMEOUT": "3600000"
  },
  "mcpServers": {
    "bacon-mqtt": {
      "command": "python3",
      "args": ["-m", "bacon_mqtt_mcp"],
      "timeout": 3600000,
      "env": {
        "MQTT_BROKER": "srv906866.hstgr.cloud",
        "MQTT_PORT": "1883"
      }
    }
  }
}
EOF
```

**Note:** If settings.json already exists, merge the configuration manually.

### Step 2.7: Copy Agent Definition

```bash
mkdir -p ~/.claude/agents
cp ~/bacon_mqtt_mcp/agents/mqtt-listener.md ~/.claude/agents/
```

### Step 2.8: Repeat for Second Ubuntu Machine

Repeat Steps 2.1-2.7 for the other Ubuntu machine (EliteBook or ZBook).

---

## Phase 3: Integration Testing

### Test 1: Point-to-Point Messaging

**Goal:** Verify basic message delivery between two machines.

#### Test 1.1: Windows → ZBook

**On ZBook (Terminal 1):**
```bash
cd ~/bacon_mqtt_mcp
python3 -c "
import asyncio
from server import wait_for_message

async def main():
    print('Waiting for message on zbook inbox...')
    result = await wait_for_message(session_id='zbook', timeout=60)
    print(f'Result: {result}')

asyncio.run(main())
"
```

**On Windows (Terminal 2):**
```powershell
cd C:\Users\Colin\bacon_mqtt_mcp
python -c "
import asyncio
from server import send_message

async def main():
    result = await send_message(
        message='Hello from Windows!',
        target_session='zbook',
        message_type='test'
    )
    print(f'Send result: {result}')

asyncio.run(main())
"
```

**Expected:** ZBook receives message within seconds.

#### Test 1.2: ZBook → EliteBook

**On EliteBook:**
```bash
python3 -c "
import asyncio
from server import wait_for_message
asyncio.run(wait_for_message(session_id='elitebook', timeout=60))
"
```

**On ZBook:**
```bash
python3 -c "
import asyncio
from server import send_message
asyncio.run(send_message('Hello from ZBook!', target_session='elitebook'))
"
```

#### Test 1.3: EliteBook → Windows

**On Windows:**
```powershell
python -c "
import asyncio
from server import wait_for_message
asyncio.run(wait_for_message(session_id='pc-left', timeout=60))
"
```

**On EliteBook:**
```bash
python3 -c "
import asyncio
from server import send_message
asyncio.run(send_message('Hello from EliteBook!', target_session='pc-left'))
"
```

---

### Test 2: Claude Code MCP Integration

**Goal:** Verify Claude Code can use the MCP tools.

#### Test 2.1: Status Check (All Machines)

In Claude Code on each machine:
```
> Call get_status from bacon-mqtt MCP server
```

Expected response includes:
- server: "bacon-mqtt-mcp"
- hostname: (machine-specific)
- mqtt_broker: "srv906866.hstgr.cloud"

#### Test 2.2: Send Message via Claude Code

**On Windows Claude Code:**
```
> Use bacon-mqtt to send a message "Test from Windows Claude" to zbook
```

**On ZBook (terminal listener):**
Should receive the message.

#### Test 2.3: Quick Message Check

**On ZBook Claude Code:**
```
> Check if there are any pending messages using bacon-mqtt
```

---

### Test 3: Background Agent Wake Test

**Goal:** Test the full h2A wake mechanism with background sub-agents.

#### Test 3.1: Spawn Listener Agent

**On ZBook Claude Code:**
```
> Spawn the mqtt-listener agent in the background to wait for messages
```

Claude should:
1. Start background sub-agent
2. Sub-agent calls wait_for_message
3. Main session remains interactive

#### Test 3.2: Send Wake Message

**On EliteBook Claude Code:**
```
> Send message to zbook: "Wake up! Please run the test suite."
```

#### Test 3.3: Verify Wake

**On ZBook Claude Code:**
After the message arrives, the background agent should complete and wake the main session with the message content.

Check if main session received notification.

---

### Test 4: Edge Cases

#### Test 4.1: Timeout Handling

**On any machine:**
```bash
python3 -c "
import asyncio
from server import wait_for_message

async def main():
    print('Testing 5-second timeout...')
    result = await wait_for_message(topic='bacon/claude/nobody/inbox', timeout=5)
    print(f'Result: {result}')
    assert result['status'] == 'timeout', 'Should have timed out'
    print('✅ Timeout test passed')

asyncio.run(main())
"
```

#### Test 4.2: Large Message

**Sender:**
```bash
python3 -c "
import asyncio
from server import send_message

large_msg = 'X' * 50000  # 50KB message
asyncio.run(send_message(large_msg, target_session='zbook'))
print('Large message sent')
"
```

**Receiver:** Should handle without issues.

#### Test 4.3: Rapid Messages

**Sender (send 10 messages quickly):**
```bash
python3 -c "
import asyncio
from server import send_message

async def main():
    for i in range(10):
        await send_message(f'Rapid message {i}', target_session='zbook')
        print(f'Sent {i}')

asyncio.run(main())
"
```

**Receiver:** May only get last message (MQTT QoS behavior). Document this.

#### Test 4.4: Invalid Topic

```bash
python3 -c "
import asyncio
from server import send_message

asyncio.run(send_message('Test', topic='invalid topic with spaces'))
"
```

Should handle gracefully (MQTT topic validation).

#### Test 4.5: Broker Disconnect During Wait

1. Start wait_for_message on ZBook
2. On Hostinger: `systemctl stop mosquitto`
3. Wait 30 seconds
4. On Hostinger: `systemctl start mosquitto`
5. Verify wait_for_message handles reconnection or reports error

#### Test 4.6: JSON vs Plain Text Messages

**Send plain text:**
```bash
mosquitto_pub -h srv906866.hstgr.cloud -t "bacon/claude/zbook/inbox" -m "Plain text message"
```

**Send JSON:**
```bash
mosquitto_pub -h srv906866.hstgr.cloud -t "bacon/claude/zbook/inbox" -m '{"custom":"payload"}'
```

Both should be handled by wait_for_message.

#### Test 4.7: Unicode/Special Characters

```bash
python3 -c "
import asyncio
from server import send_message
asyncio.run(send_message('Emoji test: 🚀 Ñoño über', target_session='zbook'))
"
```

Should preserve Unicode correctly.

#### Test 4.8: Concurrent Listeners

Start two listeners on same topic:
```bash
# Terminal 1
python3 -c "asyncio.run(wait_for_message(session_id='zbook', timeout=30))"

# Terminal 2  
python3 -c "asyncio.run(wait_for_message(session_id='zbook', timeout=30))"
```

Send one message - both should receive it (MQTT fan-out).

---

### Test 5: Full E2E Integration Test Script

Create `e2e_test.py`:

```python
#!/usr/bin/env python3
"""
End-to-End Integration Test for BACON MQTT MCP

Run from Windows PC with SSH access to other machines.
Tests messaging between all three machines.
"""

import asyncio
import subprocess
import sys
import time

MACHINES = {
    "local": {"type": "windows", "session_id": "pc-left"},
    "zbook": {"type": "ssh", "host": "bacon@zbook", "session_id": "zbook"},
    "elitebook": {"type": "ssh", "host": "bacon@elitebook", "session_id": "elitebook"},
}

MQTT_BROKER = "srv906866.hstgr.cloud"


def ssh_cmd(host, cmd):
    """Execute command via SSH."""
    full_cmd = f'ssh {host} "cd ~/bacon_mqtt_mcp && {cmd}"'
    return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)


def local_cmd(cmd):
    """Execute command locally."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=r"C:\Users\Colin\bacon_mqtt_mcp")


async def test_connectivity():
    """Test MQTT connectivity from all machines."""
    print("\n" + "="*60)
    print("TEST 1: MQTT Connectivity")
    print("="*60)
    
    results = {}
    
    # Local test
    print("\n[PC-LEFT] Testing connectivity...")
    result = local_cmd("python test_mqtt.py --quick")
    results["pc-left"] = result.returncode == 0
    print(f"  {'✅' if results['pc-left'] else '❌'} PC-LEFT: {result.stdout[:100] if results['pc-left'] else result.stderr[:100]}")
    
    # SSH tests
    for name, config in MACHINES.items():
        if config["type"] == "ssh":
            print(f"\n[{name.upper()}] Testing connectivity...")
            result = ssh_cmd(config["host"], "python3 test_mqtt.py --quick")
            results[name] = result.returncode == 0
            print(f"  {'✅' if results[name] else '❌'} {name.upper()}")
    
    return all(results.values())


async def test_point_to_point():
    """Test message delivery between each pair of machines."""
    print("\n" + "="*60)
    print("TEST 2: Point-to-Point Messaging")
    print("="*60)
    
    test_pairs = [
        ("pc-left", "zbook"),
        ("zbook", "elitebook"),
        ("elitebook", "pc-left"),
    ]
    
    results = []
    
    for sender, receiver in test_pairs:
        print(f"\n[{sender} → {receiver}]")
        
        # Start receiver
        receiver_config = MACHINES[receiver]
        if receiver_config["type"] == "ssh":
            recv_cmd = f'''python3 -c "
import asyncio
from server import wait_for_message
result = asyncio.run(wait_for_message(session_id='{receiver_config['session_id']}', timeout=10))
print('RECEIVED' if result['status'] == 'received' else 'TIMEOUT')
"'''
            recv_proc = subprocess.Popen(
                f'ssh {receiver_config["host"]} "cd ~/bacon_mqtt_mcp && {recv_cmd}"',
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
        else:
            recv_cmd = f'''python -c "
import asyncio
from server import wait_for_message
result = asyncio.run(wait_for_message(session_id='{receiver_config['session_id']}', timeout=10))
print('RECEIVED' if result['status'] == 'received' else 'TIMEOUT')
"'''
            recv_proc = subprocess.Popen(
                recv_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                text=True, cwd=r"C:\Users\Colin\bacon_mqtt_mcp"
            )
        
        await asyncio.sleep(2)  # Let receiver start
        
        # Send message
        sender_config = MACHINES[sender]
        test_msg = f"E2E test from {sender} at {time.time()}"
        
        send_cmd = f'''python3 -c "
import asyncio
from server import send_message
asyncio.run(send_message('{test_msg}', target_session='{receiver_config['session_id']}'))
print('SENT')
"'''
        
        if sender_config["type"] == "ssh":
            send_result = ssh_cmd(sender_config["host"], send_cmd)
        else:
            send_result = local_cmd(send_cmd.replace("python3", "python"))
        
        # Wait for receiver
        recv_stdout, recv_stderr = recv_proc.communicate(timeout=15)
        
        success = "RECEIVED" in recv_stdout
        results.append(success)
        print(f"  {'✅' if success else '❌'} {sender} → {receiver}")
        if not success:
            print(f"     Receiver output: {recv_stdout} {recv_stderr}")
    
    return all(results)


async def test_round_trip():
    """Test full round-trip: A → B → C → A."""
    print("\n" + "="*60)
    print("TEST 3: Round-Trip Messaging")
    print("="*60)
    
    # This is a more complex test that chains messages
    # PC sends to ZBook, ZBook sends to EliteBook, EliteBook sends back to PC
    
    print("\nStarting round-trip test: PC → ZBook → EliteBook → PC")
    print("(This test requires manual verification or automated scripts)")
    
    return True  # Placeholder - implement full automation if needed


async def main():
    print("="*60)
    print("BACON MQTT MCP - End-to-End Integration Test")
    print("="*60)
    print(f"MQTT Broker: {MQTT_BROKER}")
    print(f"Machines: {list(MACHINES.keys())}")
    
    all_passed = True
    
    # Test 1: Connectivity
    if not await test_connectivity():
        print("\n❌ Connectivity test failed. Cannot continue.")
        sys.exit(1)
    
    # Test 2: Point-to-Point
    if not await test_point_to_point():
        print("\n⚠️ Some point-to-point tests failed.")
        all_passed = False
    
    # Test 3: Round-trip
    await test_round_trip()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"{'✅ All tests passed!' if all_passed else '⚠️ Some tests failed.'}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Phase 4: Critical H2A Wake Test (5-Minute Extended Idle)

This is THE critical test that validates the core innovation: waking a Claude session after extended idle time.

### Test Overview

```
Timeline (5 minutes):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0s      30s     60s     90s     120s    ...     270s    300s
│       │       │       │       │               │       │
▼       ▼       ▼       ▼       ▼               ▼       ▼
[START] [PROG]  [PROG]  [PROG]  [PROG]  ...     [WAKE]  [TTS]
 │       │       │       │       │               │       │
 │       └───────┴───────┴───────┴───────────────┘       │
 │                                                        │
 └─ Sub-agent spawned                  Message arrives ──┘
    Blocks on wait_for_message          └─ h2A wake triggers
    Main agent goes idle                   └─ TTS announcement
    (no tokens consumed)

PROG = Progress notification (every 30s) keeps MCP connection alive
WAKE = EliteBook sends wake message
TTS  = ZBook announces success via edge-tts
```

### What This Test Validates

1. **Progress notifications reset MCP timeout** - Without them, call dies at 60s
2. **No token consumption during wait** - Main agent is truly idle
3. **h2A wake mechanism works** - Sub-agent completion wakes main
4. **Cross-machine messaging works** - EliteBook → ZBook via MQTT
5. **Extended idle is viable** - 5 minutes proves the pattern works

### Step-by-Step Execution

#### Step 4.1: Prepare ZBook (Listener)

**Option A: Using Claude Code (Recommended)**

In ZBook Claude Code, paste this prompt:

```
I need to test the h2A wake mechanism. Please:

1. Spawn a background sub-agent using the mqtt-listener agent definition
2. The sub-agent should call mcp__bacon_mqtt__wait_for_message with:
   - session_id: "zbook"
   - timeout: 330 (5.5 minutes)
3. Monitor for progress notifications (every 30s)
4. When the wake message arrives, announce via edge-tts:
   "Hello Colin! The H2A wake test completed successfully. 
    The cross-machine wake system is working!"

Start the test now.
```

**Option B: Using the test script**

```bash
# On ZBook terminal
cd ~/bacon_mqtt_mcp
python3 h2a_wake_test.py --role listener --wait-time 330 --session-id zbook
```

#### Step 4.2: Wait for Listener to Initialize

Watch for these log messages on ZBook:

```
[00:00:00] ℹ️ Starting listener on session 'zbook'
[00:00:00] ℹ️ Will wait up to 330 seconds for wake message
[00:00:00] ℹ️ Calling wait_for_message (blocking)...
[00:00:30] 🔄 Progress tick #1 - 30s elapsed, still waiting...
[00:01:00] 🔄 Progress tick #2 - 60s elapsed, still waiting...
```

**Critical Check:** If you see progress ticks continuing past 60s, the timeout reset is working!

#### Step 4.3: Send Wake Message from EliteBook (After 4.5 Minutes)

Wait until ~270 seconds have elapsed, then:

**Option A: Using Claude Code**

In EliteBook Claude Code:
```
Send a wake message to zbook using bacon-mqtt: 
"Wake up! H2A test completed successfully at [current time]"
```

**Option B: Using the test script**

```bash
# On EliteBook terminal
cd ~/bacon_mqtt_mcp
python3 h2a_wake_test.py --role sender --delay 0 --target zbook \
    --message "Wake up! H2A test at $(date)"
```

**Option C: Using mosquitto_pub**

```bash
mosquitto_pub -h srv906866.hstgr.cloud \
    -t "bacon/claude/zbook/inbox" \
    -m '{"type":"wake","content":"H2A test completed!","source":"elitebook"}'
```

#### Step 4.4: Verify Wake and TTS Announcement

On ZBook, you should see:

```
[00:04:32] 🔔 WAKE MESSAGE RECEIVED after 272.3s!
[00:04:32] ℹ️ Progress notifications sent: 9
[00:04:32] ℹ️ Message content: {'type': 'wake', 'content': '...'}
[00:04:33] 🔊 TTS: Hello Colin! The H2A wake test completed successfully...
```

And hear the TTS announcement!

#### Step 4.5: Automated Full Test

For fully automated testing:

```bash
# On ZBook - orchestrates both sides
cd ~/bacon_mqtt_mcp
python3 h2a_wake_test.py --role orchestrator --wait-time 330
```

This will:
1. Start listener locally
2. SSH to EliteBook to run sender
3. Send wake message after 300s
4. Report success and play TTS

### Success Criteria

| Checkpoint | Expected Result |
|------------|-----------------|
| Progress at 30s | ✅ "Progress tick #1 - 30s elapsed" |
| Progress at 60s | ✅ "Progress tick #2 - 60s elapsed" (proves timeout reset!) |
| Progress at 120s+ | ✅ Continued progress ticks |
| Message received | ✅ "WAKE MESSAGE RECEIVED after ~270s" |
| TTS plays | ✅ Audible announcement on ZBook |

### Failure Modes and Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Dies at 60s | Progress not resetting timeout | Check MCP SDK version, verify progress notifications are being sent |
| No wake after message sent | Topic mismatch | Verify both sides use same session_id |
| TTS not playing | edge-tts or audio issue | Install: `pip install edge-tts`, check audio output |
| SSH sender fails | SSH auth or connectivity | Test: `ssh bacon@elitebook "echo OK"` |

### Test Variations

#### Extended Test (10 minutes)
```bash
python3 h2a_wake_test.py --role listener --wait-time 630
# ... on another machine after 10 min ...
python3 h2a_wake_test.py --role sender --delay 0 --target zbook
```

#### Stress Test (Multiple rapid wakes)
```bash
# Listener
python3 h2a_wake_test.py --role listener --wait-time 60

# Sender (rapid fire)
for i in {1..5}; do
    python3 h2a_wake_test.py --role sender --delay 0 --target zbook \
        --message "Rapid wake #$i"
    sleep 2
done
```

---

## Phase 5: Production Deployment Checklist

### Per-Machine Checklist

- [ ] Python 3.10+ installed
- [ ] bacon_mqtt_mcp package installed (`pip install -e .`)
- [ ] MCP dependencies installed (mcp, aiomqtt)
- [ ] edge-tts installed for TTS announcements (`pip install edge-tts`)
- [ ] Claude Code settings.json updated with bacon-mqtt MCP server
- [ ] mqtt-listener.md agent definition in ~/.claude/agents/
- [ ] MQTT connectivity verified (`python3 test_mqtt.py --quick`)
- [ ] Claude Code restarted to load MCP server
- [ ] `get_status` returns correct hostname
- [ ] H2A wake test passed (5-minute extended idle test)

### MQTT Broker Checklist

- [ ] Mosquitto running on srv906866.hstgr.cloud
- [ ] Port 1883 accessible from all machines
- [ ] Firewall allows inbound connections
- [ ] Test publish/subscribe works

### Network Checklist

- [ ] All machines can reach srv906866.hstgr.cloud:1883
- [ ] SSH access works between machines (for automation)
- [ ] DNS resolution works (or use IP addresses)

---

## Troubleshooting

### "Connection refused" to MQTT broker

```bash
# Check if Mosquitto is running on broker
ssh root@srv906866.hstgr.cloud "systemctl status mosquitto"

# Check firewall
ssh root@srv906866.hstgr.cloud "ufw status"

# Test with telnet
telnet srv906866.hstgr.cloud 1883
```

### "Module not found: bacon_mqtt_mcp"

```bash
# Verify installation
pip show bacon_mqtt_mcp

# Or install in editable mode
cd ~/bacon_mqtt_mcp
pip install -e . --break-system-packages
```

### "MCP server not available" in Claude Code

1. Check settings.json syntax (valid JSON?)
2. Verify Python path is correct
3. Check Claude Code logs for MCP errors
4. Try running MCP server manually: `python -m bacon_mqtt_mcp`

### Messages not received

```bash
# Monitor all messages on broker
mosquitto_sub -h srv906866.hstgr.cloud -t "bacon/claude/#" -v

# Then send a test message
mosquitto_pub -h srv906866.hstgr.cloud -t "bacon/claude/zbook/inbox" -m "test"
```

### Progress notifications not resetting timeout

Check MCP SDK version and Claude Code version support for `resetTimeoutOnProgress`.

---

## Files Reference

| File | Location (Ubuntu) | Location (Windows) |
|------|-------------------|-------------------|
| server.py | ~/bacon_mqtt_mcp/server.py | C:\Users\Colin\bacon_mqtt_mcp\server.py |
| settings.json | ~/.claude/settings.json | %APPDATA%\Claude\settings.json |
| mqtt-listener.md | ~/.claude/agents/mqtt-listener.md | %USERPROFILE%\.claude\agents\mqtt-listener.md |
| test_mqtt.py | ~/bacon_mqtt_mcp/test_mqtt.py | C:\Users\Colin\bacon_mqtt_mcp\test_mqtt.py |
| e2e_test.py | ~/bacon_mqtt_mcp/e2e_test.py | C:\Users\Colin\bacon_mqtt_mcp\e2e_test.py |
| h2a_wake_test.py | ~/bacon_mqtt_mcp/h2a_wake_test.py | C:\Users\Colin\bacon_mqtt_mcp\h2a_wake_test.py |

---

## Success Criteria

The implementation is complete when:

1. ✅ All three machines can send/receive MQTT messages
2. ✅ Claude Code on each machine shows bacon-mqtt MCP server available
3. ✅ `get_status` returns correct hostname on each machine
4. ✅ Point-to-point messaging works for all pairs
5. ✅ Background mqtt-listener agent can be spawned
6. ✅ Wake mechanism triggers when message arrives
7. ✅ **H2A Wake Test passes** - 5-minute extended idle with progress keep-alive
8. ✅ TTS announcement plays on wake (edge-tts working)

---

## Next Steps After Implementation

1. **Add authentication** to MQTT broker (currently anonymous)
2. **Implement message queuing** for offline recipients
3. **Add delivery confirmation** (publish to confirmation topic)
4. **Create monitoring dashboard** for message flow
5. **Implement priority routing** for urgent messages
