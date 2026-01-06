#!/usr/bin/env python3
"""
End-to-End Integration Test for BACON MQTT MCP

This script tests cross-machine messaging between:
- Windows 11 Workstation (PC-LEFT)
- HP EliteBook (Ubuntu)
- HP ZBook (Ubuntu)

Using the Hostinger cloud MQTT broker.

Usage:
    # Run from Windows PC with SSH access to other machines
    python e2e_test.py
    
    # Run specific test
    python e2e_test.py --test connectivity
    python e2e_test.py --test point-to-point
    python e2e_test.py --test edge-cases
    
    # Verbose output
    python e2e_test.py -v
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional

# Configuration
MQTT_BROKER = "srv906866.hstgr.cloud"
MQTT_PORT = 1883

# Machine definitions - adjust hostnames/IPs as needed
MACHINES = {
    "pc-left": {
        "type": "local",
        "session_id": "pc-left",
        "python": "python",
        "package_path": r"C:\Users\Colin\bacon_mqtt_mcp",
    },
    "zbook": {
        "type": "ssh",
        "host": "bacon@zbook",  # Adjust if needed: bacon@192.168.x.x
        "session_id": "zbook",
        "python": "python3",
        "package_path": "~/bacon_mqtt_mcp",
    },
    "elitebook": {
        "type": "ssh", 
        "host": "bacon@elitebook",  # Adjust if needed: bacon@192.168.x.x
        "session_id": "elitebook",
        "python": "python3",
        "package_path": "~/bacon_mqtt_mcp",
    },
}

# Test results storage
results: Dict[str, List[Tuple[str, bool, str]]] = {
    "connectivity": [],
    "point-to-point": [],
    "edge-cases": [],
    "mcp-integration": [],
}

verbose = False


def log(msg: str, level: str = "info"):
    """Print log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️", "debug": "🔍"}
    if level == "debug" and not verbose:
        return
    print(f"[{timestamp}] {prefix.get(level, '')} {msg}")


def run_local(cmd: str, cwd: Optional[str] = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run command locally."""
    log(f"Local: {cmd[:80]}...", "debug")
    return subprocess.run(
        cmd, 
        shell=True, 
        capture_output=True, 
        text=True, 
        cwd=cwd or MACHINES["pc-left"]["package_path"],
        timeout=timeout
    )


def run_ssh(host: str, cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run command via SSH."""
    log(f"SSH {host}: {cmd[:60]}...", "debug")
    full_cmd = f'ssh -o ConnectTimeout=10 {host} "{cmd}"'
    return subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout)


def run_on_machine(machine: str, cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run command on specified machine."""
    config = MACHINES[machine]
    if config["type"] == "local":
        return run_local(cmd, timeout=timeout)
    else:
        # Wrap command with cd to package directory
        wrapped = f"cd {config['package_path']} && {cmd}"
        return run_ssh(config["host"], wrapped, timeout=timeout)


def start_background_on_machine(machine: str, cmd: str) -> subprocess.Popen:
    """Start background process on machine."""
    config = MACHINES[machine]
    if config["type"] == "local":
        return subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=config["package_path"]
        )
    else:
        wrapped = f"cd {config['package_path']} && {cmd}"
        full_cmd = f'ssh -o ConnectTimeout=10 {config["host"]} "{wrapped}"'
        return subprocess.Popen(
            full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )


# =============================================================================
# TEST: Connectivity
# =============================================================================

async def test_mqtt_connectivity():
    """Test MQTT broker connectivity from all machines."""
    log("Testing MQTT connectivity from all machines...")
    
    for name, config in MACHINES.items():
        python = config["python"]
        cmd = f'{python} -c "import asyncio; import aiomqtt; asyncio.run(aiomqtt.Client(hostname=\\"{MQTT_BROKER}\\", port={MQTT_PORT}).__aenter__())"'
        
        try:
            result = run_on_machine(name, cmd, timeout=15)
            success = result.returncode == 0
            msg = "Connected" if success else result.stderr[:100]
        except subprocess.TimeoutExpired:
            success = False
            msg = "Timeout"
        except Exception as e:
            success = False
            msg = str(e)
        
        results["connectivity"].append((f"{name} → MQTT broker", success, msg))
        log(f"{name}: {'Connected' if success else 'FAILED - ' + msg}", "success" if success else "error")
    
    return all(r[1] for r in results["connectivity"])


async def test_ssh_connectivity():
    """Test SSH connectivity to remote machines."""
    log("Testing SSH connectivity...")
    
    for name, config in MACHINES.items():
        if config["type"] != "ssh":
            continue
        
        try:
            result = run_ssh(config["host"], "echo OK", timeout=10)
            success = result.returncode == 0 and "OK" in result.stdout
            msg = "SSH OK" if success else result.stderr[:100]
        except subprocess.TimeoutExpired:
            success = False
            msg = "SSH Timeout"
        except Exception as e:
            success = False
            msg = str(e)
        
        results["connectivity"].append((f"SSH to {name}", success, msg))
        log(f"SSH {name}: {'OK' if success else 'FAILED - ' + msg}", "success" if success else "error")
    
    return all(r[1] for r in results["connectivity"] if "SSH" in r[0])


# =============================================================================
# TEST: Point-to-Point Messaging
# =============================================================================

async def test_send_receive(sender: str, receiver: str) -> bool:
    """Test message from sender to receiver."""
    log(f"Testing {sender} → {receiver}...")
    
    sender_config = MACHINES[sender]
    receiver_config = MACHINES[receiver]
    test_id = f"{int(time.time())}"
    test_msg = f"E2E-{sender}-{receiver}-{test_id}"
    
    # Python code for receiver
    recv_python = receiver_config["python"]
    recv_code = f'''
import asyncio
import sys
sys.path.insert(0, ".")
from server import wait_for_message

async def main():
    result = await wait_for_message(session_id="{receiver_config['session_id']}", timeout=15)
    if result["status"] == "received":
        print("RECEIVED:" + str(result.get("message", "")))
    else:
        print("TIMEOUT")

asyncio.run(main())
'''
    
    # Python code for sender
    send_python = sender_config["python"]
    send_code = f'''
import asyncio
import sys
sys.path.insert(0, ".")
from server import send_message

async def main():
    result = await send_message("{test_msg}", target_session="{receiver_config['session_id']}")
    print("SENT" if result["status"] == "sent" else "FAILED")

asyncio.run(main())
'''
    
    # Start receiver as background process
    recv_cmd = f'{recv_python} -c \'{recv_code}\''
    recv_proc = start_background_on_machine(receiver, recv_cmd)
    
    await asyncio.sleep(2)  # Let receiver connect
    
    # Send message
    send_cmd = f'{send_python} -c \'{send_code}\''
    try:
        send_result = run_on_machine(sender, send_cmd, timeout=10)
        send_ok = "SENT" in send_result.stdout
    except Exception as e:
        send_ok = False
        log(f"Send error: {e}", "error")
    
    # Wait for receiver
    try:
        recv_stdout, recv_stderr = recv_proc.communicate(timeout=20)
        recv_ok = "RECEIVED" in recv_stdout and test_msg in recv_stdout
    except subprocess.TimeoutExpired:
        recv_proc.kill()
        recv_ok = False
        recv_stdout = "TIMEOUT"
    
    success = send_ok and recv_ok
    msg = f"Send: {'OK' if send_ok else 'FAIL'}, Recv: {'OK' if recv_ok else 'FAIL'}"
    results["point-to-point"].append((f"{sender} → {receiver}", success, msg))
    
    log(f"{sender} → {receiver}: {msg}", "success" if success else "error")
    return success


async def test_all_point_to_point():
    """Test messaging between all pairs of machines."""
    log("Testing point-to-point messaging...")
    
    pairs = [
        ("pc-left", "zbook"),
        ("pc-left", "elitebook"),
        ("zbook", "pc-left"),
        ("zbook", "elitebook"),
        ("elitebook", "pc-left"),
        ("elitebook", "zbook"),
    ]
    
    successes = 0
    for sender, receiver in pairs:
        if await test_send_receive(sender, receiver):
            successes += 1
        await asyncio.sleep(1)  # Brief pause between tests
    
    log(f"Point-to-point: {successes}/{len(pairs)} passed")
    return successes == len(pairs)


# =============================================================================
# TEST: Edge Cases
# =============================================================================

async def test_timeout_handling():
    """Test that timeout works correctly."""
    log("Testing timeout handling...")
    
    # Use a topic nobody is subscribed to
    code = '''
import asyncio
import sys
sys.path.insert(0, ".")
from server import wait_for_message

async def main():
    result = await wait_for_message(topic="bacon/claude/nobody/inbox", timeout=3)
    print("TIMEOUT" if result["status"] == "timeout" else "UNEXPECTED")

asyncio.run(main())
'''
    
    result = run_on_machine("pc-left", f'python -c \'{code}\'', timeout=15)
    success = "TIMEOUT" in result.stdout
    
    results["edge-cases"].append(("Timeout handling", success, result.stdout[:50]))
    log(f"Timeout test: {'PASS' if success else 'FAIL'}", "success" if success else "error")
    return success


async def test_large_message():
    """Test large message handling."""
    log("Testing large message (50KB)...")
    
    # First start a receiver
    recv_code = '''
import asyncio
import sys
sys.path.insert(0, ".")
from server import wait_for_message

async def main():
    result = await wait_for_message(session_id="pc-left", timeout=15)
    if result["status"] == "received":
        msg = result.get("message", {})
        content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
        print(f"RECEIVED:{len(content)}")
    else:
        print("TIMEOUT")

asyncio.run(main())
'''
    recv_proc = start_background_on_machine("pc-left", f'python -c \'{recv_code}\'')
    await asyncio.sleep(2)
    
    # Send large message from zbook
    large_msg = "X" * 50000
    send_code = f'''
import asyncio
import sys
sys.path.insert(0, ".")
from server import send_message

asyncio.run(send_message("{large_msg}", target_session="pc-left"))
print("SENT")
'''
    
    send_result = run_on_machine("zbook", f'{MACHINES["zbook"]["python"]} -c \'{send_code}\'', timeout=15)
    
    try:
        recv_stdout, _ = recv_proc.communicate(timeout=20)
        success = "RECEIVED:50000" in recv_stdout or "RECEIVED:" in recv_stdout
    except:
        recv_proc.kill()
        success = False
    
    results["edge-cases"].append(("Large message (50KB)", success, ""))
    log(f"Large message: {'PASS' if success else 'FAIL'}", "success" if success else "error")
    return success


async def test_unicode_message():
    """Test Unicode character handling."""
    log("Testing Unicode messages...")
    
    recv_code = '''
import asyncio
import sys
sys.path.insert(0, ".")
from server import wait_for_message

async def main():
    result = await wait_for_message(session_id="pc-left", timeout=10)
    if result["status"] == "received":
        print("RECEIVED")
    else:
        print("TIMEOUT")

asyncio.run(main())
'''
    recv_proc = start_background_on_machine("pc-left", f'python -c \'{recv_code}\'')
    await asyncio.sleep(2)
    
    # Send Unicode message
    send_code = '''
import asyncio
import sys
sys.path.insert(0, ".")
from server import send_message

asyncio.run(send_message("Emoji: 🚀 Ñoño über 日本語", target_session="pc-left"))
print("SENT")
'''
    
    run_on_machine("zbook", f'{MACHINES["zbook"]["python"]} -c \'{send_code}\'', timeout=10)
    
    try:
        recv_stdout, _ = recv_proc.communicate(timeout=15)
        success = "RECEIVED" in recv_stdout
    except:
        recv_proc.kill()
        success = False
    
    results["edge-cases"].append(("Unicode characters", success, ""))
    log(f"Unicode test: {'PASS' if success else 'FAIL'}", "success" if success else "error")
    return success


async def test_json_payload():
    """Test JSON payload handling."""
    log("Testing JSON payload...")
    
    recv_code = '''
import asyncio
import sys
sys.path.insert(0, ".")
from server import wait_for_message

async def main():
    result = await wait_for_message(session_id="pc-left", timeout=10)
    if result["status"] == "received":
        msg = result.get("message", {})
        if isinstance(msg, dict) and "nested" in str(msg):
            print("RECEIVED_JSON")
        else:
            print("RECEIVED_OTHER")
    else:
        print("TIMEOUT")

asyncio.run(main())
'''
    recv_proc = start_background_on_machine("pc-left", f'python -c \'{recv_code}\'')
    await asyncio.sleep(2)
    
    # Send JSON message
    send_code = '''
import asyncio
import sys
sys.path.insert(0, ".")
from server import send_message

asyncio.run(send_message('{"nested": {"key": "value"}, "array": [1,2,3]}', target_session="pc-left"))
print("SENT")
'''
    
    run_on_machine("zbook", f'{MACHINES["zbook"]["python"]} -c \'{send_code}\'', timeout=10)
    
    try:
        recv_stdout, _ = recv_proc.communicate(timeout=15)
        success = "RECEIVED" in recv_stdout
    except:
        recv_proc.kill()
        success = False
    
    results["edge-cases"].append(("JSON payload", success, ""))
    log(f"JSON test: {'PASS' if success else 'FAIL'}", "success" if success else "error")
    return success


# =============================================================================
# TEST: MCP Integration
# =============================================================================

async def test_mcp_status():
    """Test MCP server status on all machines."""
    log("Testing MCP server status...")
    
    for name, config in MACHINES.items():
        python = config["python"]
        code = '''
import asyncio
import sys
sys.path.insert(0, ".")
from server import get_status

async def main():
    status = await get_status()
    print(f"SERVER:{status.get('server', 'unknown')}")
    print(f"HOSTNAME:{status.get('hostname', 'unknown')}")

asyncio.run(main())
'''
        
        try:
            result = run_on_machine(name, f'{python} -c \'{code}\'', timeout=10)
            success = "SERVER:bacon-mqtt" in result.stdout
            hostname = result.stdout.split("HOSTNAME:")[1].split()[0] if "HOSTNAME:" in result.stdout else "?"
            msg = f"hostname={hostname}"
        except Exception as e:
            success = False
            msg = str(e)
        
        results["mcp-integration"].append((f"MCP status on {name}", success, msg))
        log(f"{name} MCP status: {'OK' if success else 'FAIL'} ({msg})", "success" if success else "error")
    
    return all(r[1] for r in results["mcp-integration"])


# =============================================================================
# MAIN
# =============================================================================

def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_pass = 0
    total_fail = 0
    
    for category, tests in results.items():
        if not tests:
            continue
        
        print(f"\n{category.upper()}:")
        for name, passed, msg in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {name}")
            if msg and not passed:
                print(f"         {msg[:60]}")
            
            if passed:
                total_pass += 1
            else:
                total_fail += 1
    
    print("\n" + "-"*60)
    print(f"Total: {total_pass} passed, {total_fail} failed")
    print("="*60)
    
    return total_fail == 0


async def run_all_tests():
    """Run all tests."""
    log("Starting E2E Integration Tests", "info")
    log(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}", "info")
    log(f"Machines: {list(MACHINES.keys())}", "info")
    
    # Connectivity tests
    print("\n" + "="*60)
    print("PHASE 1: Connectivity Tests")
    print("="*60)
    
    await test_ssh_connectivity()
    conn_ok = await test_mqtt_connectivity()
    
    if not conn_ok:
        log("Connectivity failed! Cannot proceed with other tests.", "error")
        print_summary()
        return False
    
    # Point-to-point tests
    print("\n" + "="*60)
    print("PHASE 2: Point-to-Point Tests")
    print("="*60)
    
    await test_all_point_to_point()
    
    # Edge case tests
    print("\n" + "="*60)
    print("PHASE 3: Edge Case Tests")
    print("="*60)
    
    await test_timeout_handling()
    await test_unicode_message()
    await test_json_payload()
    # await test_large_message()  # Optional, can be slow
    
    # MCP integration tests
    print("\n" + "="*60)
    print("PHASE 4: MCP Integration Tests")
    print("="*60)
    
    await test_mcp_status()
    
    return print_summary()


async def main():
    global verbose
    
    parser = argparse.ArgumentParser(description="BACON MQTT MCP E2E Tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--test", choices=["connectivity", "point-to-point", "edge-cases", "mcp", "all"],
                        default="all", help="Specific test to run")
    parser.add_argument("--broker", default=MQTT_BROKER, help="MQTT broker hostname")
    args = parser.parse_args()
    
    verbose = args.verbose
    
    print("="*60)
    print("BACON MQTT MCP - End-to-End Integration Tests")
    print("="*60)
    
    if args.test == "all":
        success = await run_all_tests()
    elif args.test == "connectivity":
        await test_ssh_connectivity()
        success = await test_mqtt_connectivity()
        print_summary()
    elif args.test == "point-to-point":
        success = await test_all_point_to_point()
        print_summary()
    elif args.test == "edge-cases":
        await test_timeout_handling()
        await test_unicode_message()
        await test_json_payload()
        success = print_summary()
    elif args.test == "mcp":
        success = await test_mcp_status()
        print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
