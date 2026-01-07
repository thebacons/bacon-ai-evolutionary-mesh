import os
import subprocess
import sys
import argparse
from pathlib import Path

# Configuration
REMOTE_HOST = "srv906866.hstgr.cloud"
REMOTE_USER = "root"
LOCAL_SRC_DIR = Path("src/control_plane")

# Environment → Port Mapping
ENV_CONFIG = {
    "production": {"port": 8000, "dir": "/opt/bacon-ai/production"},
    "integration": {"port": 8005, "dir": "/opt/bacon-ai/integration"},
    "feature-physics": {"port": 8006, "dir": "/opt/bacon-ai/feature-physics"},
    "feature-gui": {"port": 8007, "dir": "/opt/bacon-ai/feature-gui"},
}

def run_local(cmd):
    print(f"LOCAL> {cmd}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    if result.stdout:
        print(result.stdout)
    return True

def run_remote(cmd):
    print(f"REMOTE> {cmd}")
    full_cmd = f'ssh -o StrictHostKeyChecking=no {REMOTE_USER}@{REMOTE_HOST} "{cmd}"'
    result = subprocess.run(full_cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    if result.stdout:
        print(result.stdout)
    return True

def deploy(env_name: str, from_env: str = None, rollback: bool = False):
    if env_name not in ENV_CONFIG:
        print(f"❌ Unknown environment: {env_name}")
        print(f"   Available: {list(ENV_CONFIG.keys())}")
        sys.exit(1)
    
    config = ENV_CONFIG[env_name]
    target_dir = config["dir"]
    port = config["port"]
    service_name = f"bacon-env@{port}.service"
    
    print(f"🚀 Deploying BACON-AI to {env_name} (port {port})...")
    
    if rollback:
        print("🔄 Rolling back to previous version...")
        run_remote(f"cd {target_dir} && git checkout HEAD~1")
        run_remote(f"systemctl restart {service_name}")
        print(f"✅ Rolled back {env_name}")
        return
    
    if from_env:
        # Promote from another environment
        source_dir = ENV_CONFIG[from_env]["dir"]
        print(f"📋 Promoting from {from_env} to {env_name}...")
        run_remote(f"rsync -av --delete {source_dir}/ {target_dir}/")
        run_remote(f"systemctl restart {service_name}")
        print(f"✅ Promoted {from_env} → {env_name}")
        return
    
    # Standard deployment from local
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

    # 3. Setup remote directory
    print("📁 Setting up remote directory...")
    run_remote(f"mkdir -p {target_dir}")
    
    # 4. Sync files
    print("📦 Syncing files...")
    sync_cmd = f"scp -o StrictHostKeyChecking=no -r {LOCAL_SRC_DIR}/* {REMOTE_USER}@{REMOTE_HOST}:{target_dir}/"
    if not run_local(sync_cmd):
        print("❌ Sync failed.")
        sys.exit(1)

    # 5. Setup venv and deps
    print("🔧 Setting up Python environment...")
    run_remote(f"cd {target_dir} && python3 -m venv venv")
    run_remote(f"cd {target_dir} && ./venv/bin/pip install -r requirements.txt")
    
    # 6. Upload template service (if not exists)
    template_service = LOCAL_SRC_DIR / "bacon-env@.service"
    run_local(f"scp -o StrictHostKeyChecking=no {template_service} {REMOTE_USER}@{REMOTE_HOST}:/etc/systemd/system/")
    run_remote("systemctl daemon-reload")
    
    # 7. Enable and start service
    print(f"⚡ Starting service on port {port}...")
    run_remote(f"systemctl enable {service_name}")
    run_remote(f"systemctl restart {service_name}")
    run_remote(f"systemctl status {service_name} --no-pager | head -n 10")
    
    print(f"\n✅ Deployment successful!")
    print(f"🔗 {env_name.upper()}: http://{REMOTE_HOST}:{port}/")

def main():
    parser = argparse.ArgumentParser(description="Deploy BACON-AI to multi-environment Hostinger")
    parser.add_argument("--env", default="production", help="Target environment (production, integration, feature-*)")
    parser.add_argument("--from", dest="from_env", help="Promote from another environment")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous version")
    parser.add_argument("--list", action="store_true", help="List available environments")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available environments:")
        for name, cfg in ENV_CONFIG.items():
            print(f"  {name}: port {cfg['port']} → {cfg['dir']}")
        return
    
    deploy(args.env, args.from_env, args.rollback)

if __name__ == "__main__":
    main()
