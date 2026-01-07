"""
Global Infrastructure Distribution for BACON-AI
"""
import os
import subprocess
from pathlib import Path

# Targets for infrastructure distribution
TARGETS = [
    {"host": "srv906866.hstgr.cloud", "user": "root", "port": 22},        # Hostinger
    {"host": "192.168.188.170", "user": "bacon", "port": 22},            # HP Server
    {"host": "192.168.188.163", "user": "TheBacons", "port": 9222},       # TNAS
    {"host": "192.168.178.168", "user": "colin", "port": 22},            # Windows 11 PC (WSL)
    {"host": "192.168.178.73", "user": "bacon", "port": 22},             # elitebook
    {"host": "192.168.178.112", "user": "colin", "port": 22},            # Dell Laptop
    {"host": "192.168.178.29", "user": "colin", "port": 22},             # Mele PC
]

LOCAL_ENV = r"C:\Users\colin\.claude\.env"
LOCAL_SKILL_DIR = r"C:\Users\colin\.claude\skills\bacon-mem0-memory"

def run_command(cmd, timeout=30):
    print(f"RUN> {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ Timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def distribute():
    print("🌍 Starting Global Infrastructure Distribution for BACON-AI...")
    
    # Common SSH options for non-interactive distribution
    ssh_opts = "-o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5"
    
    for target in TARGETS:
        host = target["host"]
        user = target["user"]
        port = target["port"]
        
        print(f"\n--- Processing {user}@{host} (Port {port}) ---")
        
        # 1. Ensure .claude and .claude/skills exist
        mkdir_cmd = f'ssh {ssh_opts} -p {port} {user}@{host} "mkdir -p ~/.claude/skills"'
        if not run_command(mkdir_cmd):
            print(f"⚠️ Could not access {host}. Skipping.")
            continue
            
        # 2. Copy .env
        env_cmd = f'scp {ssh_opts} -P {port} "{LOCAL_ENV}" {user}@{host}:~/.claude/.env'
        if run_command(env_cmd):
            print(f"✅ Copied .env to {host}")
            
        # 3. Copy Skill directory
        skill_cmd = f'scp {ssh_opts} -P {port} -r "{LOCAL_SKILL_DIR}" {user}@{host}:~/.claude/skills/'
        if run_command(skill_cmd):
            print(f"✅ Copied bacon-mem0-memory skill to {host}")


    print("\n✅ Distribution process complete.")

if __name__ == "__main__":
    distribute()
