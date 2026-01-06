#!/usr/bin/env python3
"""
H2A Wake Test - The Critical Validation

This test validates the core innovation:
1. Main Claude session spawns background sub-agent
2. Sub-agent calls wait_for_message (blocks for 5+ minutes)
3. MCP sends progress notifications every 30s to keep alive
4. Main session goes idle (no tokens consumed)
5. After delay, message arrives via MQTT
6. Sub-agent completes → h2A wake triggers
7. Main session resumes and announces success via TTS

This is the "proof of concept" test for cross-machine Claude wake.

Usage:
    # On ZBook - run the listener/waiter
    python h2a_wake_test.py --role listener --wait-time 300
    
    # On EliteBook or Windows - send wake message after delay
    python h2a_wake_test.py --role sender --delay 300 --target zbook
    
    # Full automated test (runs both with timing)
    python h2a_wake_test.py --role orchestrator --wait-time 300
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Optional

# Configuration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "srv906866.hstgr.cloud")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))

# TTS Configuration (using Colin's edge-tts preference)
TTS_VOICE = "en-GB-SoniaNeural"  # Elisabeth voice from Colin's preferences
TTS_TOOL = "edge-tts"


def log(msg: str, level: str = "info"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    icons = {"info": "ℹ️", "success": "✅", "error": "❌", "progress": "🔄", "wake": "🔔", "tts": "🔊"}
    print(f"[{timestamp}] {icons.get(level, '•')} {msg}")


async def speak_announcement(message: str) -> bool:
    """
    Announce message via TTS using edge-tts.
    
    This mimics the elisabeth_pre_tool voice protocol from Colin's preferences.
    """
    log(f"TTS: {message}", "tts")
    
    try:
        # Try edge-tts first
        import edge_tts
        
        communicate = edge_tts.Communicate(message, TTS_VOICE)
        audio_file = "/tmp/h2a_wake_announcement.mp3"
        await communicate.save(audio_file)
        
        # Play the audio
        if sys.platform == "linux":
            # Try various Linux audio players
            for player in ["mpv", "ffplay", "aplay", "paplay"]:
                try:
                    result = subprocess.run(
                        [player, "-nodisp" if player == "ffplay" else "", audio_file],
                        capture_output=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        return True
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            # Fallback: just log that we would speak
            log("(Audio playback not available, but TTS generated)", "info")
            return True
            
        elif sys.platform == "win32":
            os.system(f'start /min wmplayer "{audio_file}"')
            return True
            
        return True
        
    except ImportError:
        log("edge-tts not installed, using espeak fallback", "info")
        try:
            subprocess.run(["espeak", message], capture_output=True, timeout=30)
            return True
        except:
            log("No TTS available, announcement logged only", "info")
            return False
    except Exception as e:
        log(f"TTS error: {e}", "error")
        return False


async def run_listener(wait_time: int, session_id: str) -> dict:
    """
    Run the listener side of the test.
    
    This simulates what the background sub-agent would do:
    1. Call wait_for_message with long timeout
    2. Progress notifications keep connection alive
    3. When message arrives, return and trigger wake
    
    Returns result dict with timing information.
    """
    log(f"Starting listener on session '{session_id}'", "info")
    log(f"Will wait up to {wait_time} seconds for wake message", "info")
    log(f"Progress notifications every 30s will keep connection alive", "info")
    
    # Import our MCP server functions
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from server import wait_for_message
    
    start_time = time.time()
    progress_count = 0
    
    # Custom progress reporter that logs
    async def progress_monitor():
        nonlocal progress_count
        while True:
            await asyncio.sleep(30)
            progress_count += 1
            elapsed = int(time.time() - start_time)
            log(f"Progress tick #{progress_count} - {elapsed}s elapsed, still waiting...", "progress")
    
    # Start progress monitor
    progress_task = asyncio.create_task(progress_monitor())
    
    try:
        # This is the blocking call that would keep sub-agent alive
        log("Calling wait_for_message (blocking)...", "info")
        result = await wait_for_message(
            session_id=session_id,
            timeout=wait_time
        )
        
        elapsed = time.time() - start_time
        
        if result["status"] == "received":
            log(f"🔔 WAKE MESSAGE RECEIVED after {elapsed:.1f}s!", "wake")
            log(f"Progress notifications sent: {progress_count}", "info")
            log(f"Message content: {result.get('message', {})}", "info")
            
            # Announce success via TTS
            announcement = (
                f"Hello Colin! The H2A wake test completed successfully. "
                f"I waited for {int(elapsed)} seconds with {progress_count} progress updates, "
                f"then received the wake message. The cross-machine wake system is working!"
            )
            await speak_announcement(announcement)
            
            return {
                "status": "success",
                "elapsed_seconds": elapsed,
                "progress_count": progress_count,
                "message": result.get("message"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            log(f"Timeout after {elapsed:.1f}s - no wake message received", "error")
            return {
                "status": "timeout",
                "elapsed_seconds": elapsed,
                "progress_count": progress_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    finally:
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass


async def run_sender(delay: int, target_session: str, message: Optional[str] = None) -> dict:
    """
    Run the sender side of the test.
    
    Waits for specified delay, then sends wake message.
    This simulates EliteBook sending a message to wake ZBook.
    """
    log(f"Sender initialized - will send wake message to '{target_session}' in {delay}s", "info")
    
    # Import our MCP server functions
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from server import send_message
    
    # Countdown with periodic updates
    remaining = delay
    while remaining > 0:
        if remaining > 60:
            log(f"Waiting... {remaining}s until wake message", "info")
            await asyncio.sleep(60)
            remaining -= 60
        elif remaining > 10:
            log(f"Waiting... {remaining}s until wake message", "info")
            await asyncio.sleep(10)
            remaining -= 10
        else:
            await asyncio.sleep(remaining)
            remaining = 0
    
    # Send the wake message
    wake_message = message or f"WAKE! Test completed at {datetime.now(timezone.utc).isoformat()}"
    
    log(f"Sending wake message to {target_session}...", "wake")
    
    result = await send_message(
        message=wake_message,
        target_session=target_session,
        message_type="wake"
    )
    
    if result["status"] == "sent":
        log(f"Wake message sent successfully!", "success")
        return {"status": "sent", "target": target_session, "timestamp": result["timestamp"]}
    else:
        log(f"Failed to send wake message: {result}", "error")
        return {"status": "error", "error": str(result)}


async def run_orchestrator(wait_time: int, sender_machine: str = "elitebook") -> dict:
    """
    Orchestrate the full test from a single machine.
    
    This runs the listener locally and SSHs to another machine to send the wake.
    Used for automated testing.
    """
    log("Orchestrator mode - running full h2A wake test", "info")
    log(f"Listener will wait {wait_time}s, sender will trigger after {wait_time - 30}s", "info")
    
    import socket
    hostname = socket.gethostname().lower()
    
    # Determine which machine we're on and where to send from
    if "zbook" in hostname:
        listener_session = "zbook"
        sender_host = f"bacon@{sender_machine}"
    elif "elitebook" in hostname:
        listener_session = "elitebook"
        sender_host = "bacon@zbook"
    else:
        listener_session = "pc-left"
        sender_host = "bacon@zbook"
    
    log(f"Running listener as '{listener_session}'", "info")
    log(f"Will SSH to '{sender_host}' to send wake message", "info")
    
    # Calculate sender delay (send 30s before listener timeout)
    sender_delay = max(wait_time - 30, 10)
    
    async def ssh_sender():
        """Run sender via SSH on remote machine."""
        await asyncio.sleep(5)  # Let listener start first
        
        cmd = (
            f"cd ~/bacon_mqtt_mcp && python3 h2a_wake_test.py "
            f"--role sender --delay {sender_delay} --target {listener_session}"
        )
        
        log(f"Starting SSH sender: {sender_host}", "info")
        
        proc = await asyncio.create_subprocess_shell(
            f'ssh {sender_host} "{cmd}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            log("SSH sender completed successfully", "success")
        else:
            log(f"SSH sender error: {stderr.decode()}", "error")
    
    # Run both concurrently
    listener_task = asyncio.create_task(run_listener(wait_time, listener_session))
    sender_task = asyncio.create_task(ssh_sender())
    
    # Wait for listener (sender will complete on its own)
    result = await listener_task
    
    return result


async def run_interactive_test():
    """
    Run interactive test with step-by-step prompts.
    
    Useful for manual testing with real Claude Code sessions.
    """
    log("=" * 60, "info")
    log("H2A WAKE TEST - Interactive Mode", "info")
    log("=" * 60, "info")
    
    print("""
This test validates the cross-machine Claude wake system.

SETUP REQUIRED:
1. On ZBook: Have Claude Code running with bacon-mqtt MCP loaded
2. On EliteBook/Windows: Ready to send wake message

TEST STEPS:
1. In ZBook Claude Code, say:
   "Spawn mqtt-listener agent in background to wait for messages"
   
2. Wait for Claude to confirm the background agent is running

3. On EliteBook, run:
   python h2a_wake_test.py --role sender --delay 10 --target zbook

4. Watch ZBook Claude Code wake up and process the message

5. Main agent should announce success via TTS

Press Enter when ready to start sender (or Ctrl+C to cancel)...
""")
    
    input()
    
    # Run sender with short delay for interactive testing
    result = await run_sender(delay=10, target_session="zbook")
    
    print(f"\nSender result: {json.dumps(result, indent=2)}")


# =============================================================================
# Claude Code Integration - Sub-Agent Script
# =============================================================================

LISTENER_AGENT_SCRIPT = """
# H2A Wake Test - Listener Sub-Agent Instructions

You are a test agent validating the h2A wake mechanism.

## Your Task

1. Call the bacon-mqtt MCP tool `wait_for_message`:
   - session_id: "{session_id}"
   - timeout: {timeout}

2. This call will BLOCK for up to {timeout} seconds
   - Progress notifications every 30s keep you alive
   - You consume NO tokens while waiting
   
3. When a wake message arrives:
   - Report the message content to main agent
   - Include timing information (how long you waited)
   
4. If timeout occurs:
   - Report that no message was received
   - Include how long you waited

## Expected Behavior

The MCP server sends progress notifications every 30 seconds:
- "Listening on bacon/claude/{session_id}/inbox... (30s elapsed)"
- "Listening on bacon/claude/{session_id}/inbox... (60s elapsed)"
- etc.

These prevent timeout and keep the connection alive.

When a message arrives, you'll receive:
{{
    "status": "received",
    "message": <the wake message>,
    "elapsed_seconds": <how long you waited>,
    "timestamp": <when message arrived>
}}

## Now Execute

Call wait_for_message and report the result.
"""


def generate_claude_code_prompt(session_id: str, timeout: int) -> str:
    """Generate prompt for Claude Code to run the listener test."""
    return f"""
# H2A Wake Test Instructions

Please execute the following test to validate cross-machine wake:

## Step 1: Spawn Background Listener

Run this command to spawn a background sub-agent:

```
Spawn a background agent that calls mcp__bacon_mqtt__wait_for_message 
with session_id="{session_id}" and timeout={timeout}
```

## Step 2: Monitor Progress

The background agent will send progress updates every 30 seconds.
You should see messages like:
- "Listening on bacon/claude/{session_id}/inbox... (30s elapsed)"

## Step 3: Receive Wake Message

When a message arrives from another machine, the background agent 
will complete and wake you with the message content.

## Step 4: Announce Success

When you receive the wake notification, use edge-tts to announce:

"Hello Colin! The H2A wake test completed successfully after [X] seconds. 
The cross-machine wake system is working!"

---

Now begin by spawning the listener agent.
"""


# =============================================================================
# Main
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="H2A Wake Test - Validate cross-machine Claude wake",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run listener (on ZBook)
  python h2a_wake_test.py --role listener --wait-time 300
  
  # Run sender after 5 min delay (on EliteBook)  
  python h2a_wake_test.py --role sender --delay 300 --target zbook
  
  # Full orchestrated test
  python h2a_wake_test.py --role orchestrator --wait-time 300
  
  # Interactive test with prompts
  python h2a_wake_test.py --role interactive
  
  # Generate Claude Code prompt
  python h2a_wake_test.py --role prompt --session-id zbook --wait-time 300
"""
    )
    
    parser.add_argument(
        "--role", 
        choices=["listener", "sender", "orchestrator", "interactive", "prompt"],
        required=True,
        help="Role to play in the test"
    )
    parser.add_argument(
        "--wait-time",
        type=int,
        default=300,
        help="How long listener waits (seconds, default: 300 = 5 min)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=300,
        help="Sender delay before sending wake (seconds)"
    )
    parser.add_argument(
        "--target",
        default="zbook",
        help="Target session for sender (default: zbook)"
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session ID for listener (default: hostname)"
    )
    parser.add_argument(
        "--message",
        default=None,
        help="Custom wake message"
    )
    
    args = parser.parse_args()
    
    # Determine session ID
    if args.session_id:
        session_id = args.session_id
    else:
        import socket
        hostname = socket.gethostname().lower()
        session_id = hostname.replace(".", "-")
    
    print("=" * 60)
    print("H2A WAKE TEST - Cross-Machine Claude Wake Validation")
    print("=" * 60)
    print(f"Role: {args.role}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Session ID: {session_id}")
    print("=" * 60)
    
    if args.role == "listener":
        result = await run_listener(args.wait_time, session_id)
        print(f"\nResult: {json.dumps(result, indent=2)}")
        
    elif args.role == "sender":
        result = await run_sender(args.delay, args.target, args.message)
        print(f"\nResult: {json.dumps(result, indent=2)}")
        
    elif args.role == "orchestrator":
        result = await run_orchestrator(args.wait_time)
        print(f"\nResult: {json.dumps(result, indent=2)}")
        
    elif args.role == "interactive":
        await run_interactive_test()
        
    elif args.role == "prompt":
        prompt = generate_claude_code_prompt(session_id, args.wait_time)
        print(prompt)
        
        # Also save to file
        with open("/tmp/h2a_wake_test_prompt.md", "w") as f:
            f.write(prompt)
        print(f"\nPrompt saved to /tmp/h2a_wake_test_prompt.md")


if __name__ == "__main__":
    asyncio.run(main())
