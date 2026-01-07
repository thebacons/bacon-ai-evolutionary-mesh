import os
import subprocess
import sys
from pathlib import Path

# Configuration
REMOTE_HOST = "srv906866.hstgr.cloud"
REMOTE_USER = "root"
TARGET_DIR = "/home/bacon/bacon-control-plane"
LOCAL_SRC_DIR = Path("src/control_plane")
SERVICE_NAME = "bacon-control.service"
LOCAL_SERVICE_FILE = LOCAL_SRC_DIR / SERVICE_NAME

def run_local(cmd):
    print(f"LOCAL> {cmd}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True

def run_remote(cmd):
    print(f"REMOTE> {cmd}")
    full_cmd = f'ssh -o StrictHostKeyChecking=no {REMOTE_USER}@{REMOTE_HOST} "{cmd}"'
    result = subprocess.run(full_cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True

def main():
    print("🚀 Starting BACON-AI Control Plane Deployment to Hostinger...")

    # 1. Clean local cache
    print("🧹 Cleaning local pycache...")
    for p in LOCAL_SRC_DIR.rglob("__pycache__"):
        import shutil
        shutil.rmtree(p)

    # 2. Build Dashboard
    print("🛠️ Building Dashboard...")
    dashboard_dir = Path("src/dashboard")
    if not run_local(f"cd {dashboard_dir} && npm run build"):
        print("❌ Dashboard build failed.")
        sys.exit(1)

    # 3. Sync files to Hostinger
    print("📦 Syncing files to Hostinger...")
    # Sync backend (includes static folder if built there)
    sync_cmd = f"scp -o StrictHostKeyChecking=no -r {LOCAL_SRC_DIR}/* {REMOTE_USER}@{REMOTE_HOST}:{TARGET_DIR}/"
    if not run_local(sync_cmd):
        print("❌ Backend sync failed.")
        sys.exit(1)

    # 3. Handle permissions and environment
    print("🔧 Setting up remote environment...")
    setup_cmds = [
        f"mkdir -p {TARGET_DIR}",
        f"cd {TARGET_DIR} && python3 -m venv venv",
        f"cd {TARGET_DIR} && ./venv/bin/pip install -r requirements.txt"
    ]
    for cmd in setup_cmds:
        if not run_remote(cmd):
            print(f"⚠️ Remote setup warning (might already be set): {cmd}")

    # 4. Upload Systemd Service
    print("⚙️  Configuring Systemd service...")
    # Upload the service file
    service_sync_cmd = f"scp -o StrictHostKeyChecking=no {LOCAL_SERVICE_FILE} {REMOTE_USER}@{REMOTE_HOST}:/tmp/{SERVICE_NAME}.tmp"
    if not run_local(service_sync_cmd):
        print("❌ Service file sync failed.")
        sys.exit(1)
        
    move_service_cmd = f"mv /tmp/{SERVICE_NAME}.tmp /etc/systemd/system/{SERVICE_NAME}"
    if not run_remote(move_service_cmd):
        print("❌ Failed to move service file to /etc/systemd/system/")
        sys.exit(1)

    # 5. Start Service
    print("⚡ Starting and enabling service...")
    start_cmds = [
        "systemctl daemon-reload",
        f"systemctl enable {SERVICE_NAME}",
        f"systemctl restart {SERVICE_NAME}"
    ]
    for cmd in start_cmds:
        run_remote(cmd)
        
    # Check status
    run_remote(f"systemctl status {SERVICE_NAME} --no-pager | head -n 12")

    print("\n✅ Deployment successful!")
    print(f"🔗 API docs accessible at: http://{REMOTE_HOST}:8000/docs")

if __name__ == "__main__":
    main()
