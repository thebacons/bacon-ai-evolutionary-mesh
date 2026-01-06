# CLAUDE CODE CLI: BACON MQTT MCP Implementation Instructions

## Mission

Implement the BACON MQTT MCP cross-machine wake system across Colin's infrastructure and validate with the H2A wake test.

**Objective:** Enable Claude sessions on different machines to wake each other via MQTT messaging, proving the h2A queue wake mechanism works after extended idle periods.

---

## Infrastructure

| Machine | OS | Access | Session ID |
|---------|-----|--------|------------|
| Windows 11 PC | Windows | Local (you're here) | `pc-left` |
| HP ZBook | Ubuntu | `ssh bacon@zbook` | `zbook` |
| HP EliteBook | Ubuntu | `ssh bacon@elitebook` | `elitebook` |
| MQTT Broker | Ubuntu | `ssh root@srv906866.hstgr.cloud` | N/A |

---

## Phase 1: Local Setup (Windows 11 PC)

### 1.1 Create Package Directory

```powershell
mkdir C:\Users\Colin\bacon_mqtt_mcp
cd C:\Users\Colin\bacon_mqtt_mcp
```

### 1.2 Download/Create Package Files

The package zip should be available. Extract it to `C:\Users\Colin\bacon_mqtt_mcp\` or create the files from the artifacts provided.

Required files:
- `server.py` - Main MCP server
- `__init__.py` - Package init
- `__main__.py` - Entry point
- `requirements.txt` - Dependencies
- `test_mqtt.py` - Basic tests
- `e2e_test.py` - Cross-machine tests
- `h2a_wake_test.py` - Critical wake test
- `agents/mqtt-listener.md` - Sub-agent definition
- `config/settings.example.json` - Example config

### 1.3 Install Dependencies

```powershell
cd C:\Users\Colin\bacon_mqtt_mcp
pip install mcp aiomqtt edge-tts
pip install -e .
```

### 1.4 Test MQTT Connectivity

```powershell
python test_mqtt.py --broker srv906866.hstgr.cloud --quick
```

**Expected:** `✅ Connected to MQTT broker`

If connection fails, verify the MQTT broker is running:
```powershell
ssh root@srv906866.hstgr.cloud "systemctl status mosquitto"
```

### 1.5 Configure Claude Code (Windows)

Find Claude Code settings location and add MCP server config:

```powershell
# Check common locations
dir %APPDATA%\Claude\
dir %USERPROFILE%\.claude\
```

Edit `settings.json` to add:

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

### 1.6 Copy Agent Definition

```powershell
mkdir %USERPROFILE%\.claude\agents 2>nul
copy agents\mqtt-listener.md %USERPROFILE%\.claude\agents\
```

### 1.7 Verify Local Setup

```powershell
python -c "from bacon_mqtt_mcp.server import get_status; import asyncio; print(asyncio.run(get_status()))"
```

**Expected:** Server info with hostname

---

## Phase 2: ZBook Setup (via SSH)

### 2.1 SSH to ZBook

```powershell
ssh bacon@zbook
```

### 2.2 Create Package Directory

```bash
mkdir -p ~/bacon_mqtt_mcp
cd ~/bacon_mqtt_mcp
```

### 2.3 Transfer Package Files

**Option A: SCP from Windows** (run from Windows terminal)
```powershell
scp -r C:\Users\Colin\bacon_mqtt_mcp\* bacon@zbook:~/bacon_mqtt_mcp/
```

**Option B: Create files directly on ZBook**

Create each file. The essential ones are:

**server.py** - The main MCP server (copy full content from package)

**__init__.py:**
```python
from .server import mcp, wait_for_message, send_message, check_messages, get_status
__version__ = "1.0.0"
```

**__main__.py:**
```python
from .server import mcp
if __name__ == "__main__":
    mcp.run()
```

**requirements.txt:**
```
mcp>=1.0.0
aiomqtt>=2.0.0
edge-tts>=6.0.0
```

### 2.4 Install Dependencies

```bash
cd ~/bacon_mqtt_mcp
pip install --break-system-packages -r requirements.txt
pip install --break-system-packages -e .
```

### 2.5 Test MQTT Connectivity

```bash
python3 test_mqtt.py --broker srv906866.hstgr.cloud --quick
```

### 2.6 Configure Claude Code (ZBook)

```bash
mkdir -p ~/.claude/agents

# Create/update settings.json
cat > ~/.claude/settings.json << 'EOF'
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

# Copy agent definition
cp ~/bacon_mqtt_mcp/agents/mqtt-listener.md ~/.claude/agents/
```

**Note:** If `~/.claude/settings.json` already exists with other config, merge manually.

### 2.7 Verify ZBook Setup

```bash
python3 -c "from bacon_mqtt_mcp.server import get_status; import asyncio; print(asyncio.run(get_status()))"
```

**Expected:** `{'server': 'bacon-mqtt-mcp', 'hostname': 'zbook', ...}`

### 2.8 Exit SSH

```bash
exit
```

---

## Phase 3: EliteBook Setup (via SSH)

### 3.1 SSH to EliteBook

```powershell
ssh bacon@elitebook
```

### 3.2 Repeat ZBook Steps

Execute the same steps as Phase 2 (2.2 through 2.7) on EliteBook.

Quick version:
```bash
# Create directory
mkdir -p ~/bacon_mqtt_mcp
cd ~/bacon_mqtt_mcp

# Transfer files (from another terminal on Windows)
# scp -r C:\Users\Colin\bacon_mqtt_mcp\* bacon@elitebook:~/bacon_mqtt_mcp/

# Install
pip install --break-system-packages mcp aiomqtt edge-tts
pip install --break-system-packages -e .

# Configure Claude Code
mkdir -p ~/.claude/agents
cat > ~/.claude/settings.json << 'EOF'
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

cp ~/bacon_mqtt_mcp/agents/mqtt-listener.md ~/.claude/agents/

# Verify
python3 -c "from bacon_mqtt_mcp.server import get_status; import asyncio; print(asyncio.run(get_status()))"
```

### 3.3 Exit SSH

```bash
exit
```

---

## Phase 4: Basic Connectivity Tests

### 4.1 Test Point-to-Point Messaging

**Terminal 1 (Windows) - Start receiver:**
```powershell
cd C:\Users\Colin\bacon_mqtt_mcp
python -c "import asyncio; from server import wait_for_message; print(asyncio.run(wait_for_message(session_id='pc-left', timeout=30)))"
```

**Terminal 2 (Windows) - SSH to ZBook and send:**
```powershell
ssh bacon@zbook "cd ~/bacon_mqtt_mcp && python3 -c \"import asyncio; from server import send_message; print(asyncio.run(send_message('Hello from ZBook!', target_session='pc-left')))\""
```

**Expected:** Windows terminal shows received message.

### 4.2 Test All Pairs

Run the E2E test suite:
```powershell
cd C:\Users\Colin\bacon_mqtt_mcp
python e2e_test.py --test connectivity
python e2e_test.py --test point-to-point
```

**Expected:** All connectivity tests pass, most point-to-point tests pass.

---

## Phase 5: H2A Wake Test (Critical Validation)

This is THE test that proves the architecture works.

### 5.1 Understand What We're Testing

```
Timeline:
0s      30s     60s     90s    ...    270s    300s
│        │       │       │              │       │
[START]  [PROG]  [PROG]  [PROG]  ...   [WAKE]  [TTS]

- Sub-agent spawns and blocks on wait_for_message
- Progress notifications every 30s keep MCP alive
- Main agent is IDLE (no tokens consumed)
- After ~5 minutes, wake message arrives
- Sub-agent completes → h2A wake triggers
- TTS announces success
```

### 5.2 Run the Test

**Option A: Fully Automated (Recommended)**

SSH to ZBook and run orchestrator:
```powershell
ssh bacon@zbook "cd ~/bacon_mqtt_mcp && python3 h2a_wake_test.py --role orchestrator --wait-time 330"
```

This will:
1. Start listener on ZBook
2. SSH to EliteBook to send wake after ~5 min
3. Report success and play TTS

**Option B: Manual Two-Terminal Test**

**Terminal 1 - ZBook Listener:**
```powershell
ssh bacon@zbook "cd ~/bacon_mqtt_mcp && python3 h2a_wake_test.py --role listener --wait-time 330 --session-id zbook"
```

Watch for progress ticks:
```
[00:00:30] 🔄 Progress tick #1 - 30s elapsed, still waiting...
[00:01:00] 🔄 Progress tick #2 - 60s elapsed, still waiting...  ← CRITICAL: Past 60s!
[00:01:30] 🔄 Progress tick #3 - 90s elapsed, still waiting...
...
```

**Terminal 2 - EliteBook Sender (after ~4.5 minutes):**
```powershell
ssh bacon@elitebook "cd ~/bacon_mqtt_mcp && python3 h2a_wake_test.py --role sender --delay 0 --target zbook --message 'Wake up ZBook! H2A test succeeded!'"
```

**Terminal 1 should show:**
```
[00:04:32] 🔔 WAKE MESSAGE RECEIVED after 272.3s!
[00:04:32] ℹ️ Progress notifications sent: 9
[00:04:33] 🔊 TTS: Hello Colin! The H2A wake test completed successfully...
```

### 5.3 Verify Success Criteria

| Checkpoint | What to Look For |
|------------|------------------|
| Progress at 30s | `Progress tick #1 - 30s elapsed` |
| Progress at 60s | `Progress tick #2 - 60s elapsed` ← **PROVES TIMEOUT RESET!** |
| Progress continues | Ticks keep coming every 30s |
| Wake received | `WAKE MESSAGE RECEIVED after ~270s` |
| TTS plays | Audible announcement on ZBook speakers |

### 5.4 Quick Validation Test (60 seconds)

For faster iteration:
```powershell
# Terminal 1 - ZBook listener (60s timeout)
ssh bacon@zbook "cd ~/bacon_mqtt_mcp && python3 h2a_wake_test.py --role listener --wait-time 70 --session-id zbook"

# Wait 45 seconds, then Terminal 2 - EliteBook sender
ssh bacon@elitebook "cd ~/bacon_mqtt_mcp && python3 h2a_wake_test.py --role sender --delay 0 --target zbook"
```

---

## Phase 6: Claude Code Integration Test

After basic tests pass, test with actual Claude Code sessions.

### 6.1 Restart Claude Code on All Machines

The MCP server config needs Claude Code restart to take effect.

### 6.2 Test MCP Server in Claude Code

In Claude Code on each machine, ask:
```
Show me the status of the bacon-mqtt MCP server
```

**Expected:** Returns server info with correct hostname.

### 6.3 Test Background Agent Spawn

In Claude Code on ZBook:
```
Spawn the mqtt-listener agent in the background to wait for messages from other machines. Use session_id "zbook" and timeout 120 seconds.
```

Then from EliteBook Claude Code:
```
Send a message to zbook using bacon-mqtt: "Hello from EliteBook Claude!"
```

ZBook Claude should wake and report the message.

---

## Troubleshooting

### MQTT Connection Failed

```bash
# Check broker is running
ssh root@srv906866.hstgr.cloud "systemctl status mosquitto"

# Check port is open
ssh root@srv906866.hstgr.cloud "netstat -tlnp | grep 1883"

# Test with mosquitto client
ssh root@srv906866.hstgr.cloud "mosquitto_pub -h localhost -t test -m hello"
```

### Module Not Found

```bash
# On Ubuntu
pip install --break-system-packages -e ~/bacon_mqtt_mcp

# Verify
python3 -c "import bacon_mqtt_mcp; print('OK')"
```

### MCP Server Not Available in Claude Code

1. Check settings.json syntax is valid JSON
2. Verify Python path is correct (`python` vs `python3`)
3. Restart Claude Code completely
4. Check Claude Code logs for MCP errors

### TTS Not Playing

```bash
# Install edge-tts
pip install --break-system-packages edge-tts

# Test manually
python3 -c "import edge_tts; import asyncio; asyncio.run(edge_tts.Communicate('Hello Colin', 'en-GB-SoniaNeural').save('/tmp/test.mp3'))"
mpv /tmp/test.mp3
```

### Progress Ticks Stop at 60s

The MCP timeout reset may not be working. Check:
1. MCP SDK version (`pip show mcp`)
2. Claude Code version
3. Verify progress notifications are being sent (check server logs)

---

## Success Checklist

After completing all phases, verify:

- [ ] Windows PC: `test_mqtt.py --quick` passes
- [ ] ZBook: `test_mqtt.py --quick` passes  
- [ ] EliteBook: `test_mqtt.py --quick` passes
- [ ] Windows → ZBook message delivery works
- [ ] ZBook → EliteBook message delivery works
- [ ] EliteBook → Windows message delivery works
- [ ] H2A wake test: Progress ticks continue past 60s
- [ ] H2A wake test: Wake message received after ~5 min
- [ ] H2A wake test: TTS announcement plays
- [ ] Claude Code: MCP server status works on all machines
- [ ] Claude Code: Background agent spawn works

---

## Summary Commands

```powershell
# === WINDOWS SETUP ===
cd C:\Users\Colin\bacon_mqtt_mcp
pip install mcp aiomqtt edge-tts -e .
python test_mqtt.py --quick

# === ZBOOK SETUP (via SSH) ===
ssh bacon@zbook
mkdir -p ~/bacon_mqtt_mcp && cd ~/bacon_mqtt_mcp
# (transfer files via scp)
pip install --break-system-packages mcp aiomqtt edge-tts -e .
python3 test_mqtt.py --quick
exit

# === ELITEBOOK SETUP (via SSH) ===
ssh bacon@elitebook
mkdir -p ~/bacon_mqtt_mcp && cd ~/bacon_mqtt_mcp
# (transfer files via scp)
pip install --break-system-packages mcp aiomqtt edge-tts -e .
python3 test_mqtt.py --quick
exit

# === RUN H2A WAKE TEST ===
ssh bacon@zbook "cd ~/bacon_mqtt_mcp && python3 h2a_wake_test.py --role orchestrator --wait-time 330"
```

---

## End State

When complete, you will have:

1. **Three machines** with bacon-mqtt-mcp installed
2. **Cross-machine messaging** working via MQTT
3. **H2A wake mechanism** validated with 5-minute test
4. **TTS announcements** working on wake
5. **Claude Code integration** ready for production use

Colin can then use this for the BACON-AI multi-agent orchestration system!
