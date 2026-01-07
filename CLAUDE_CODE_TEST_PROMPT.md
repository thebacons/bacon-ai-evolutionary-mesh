# BACON-AI Feature Testing Prompt for Claude-Code

## Objective
Test the BACON-AI Feature Environment on port 8006 by sending heartbeats and verifying the dashboard.

## Steps

### 1. Send Test Heartbeats
Run the following to register agents on the feature environment:

```bash
cd ~/bacon-ai/projects/bacon-ai-evolutionary-mesh

# Send heartbeats to feature environment (port 8006)
python src/control_plane/simulate_heartbeat.py --host srv906866.hstgr.cloud --port 8006 --count 5

# Or manually via curl:
curl -X POST http://srv906866.hstgr.cloud:8006/api/agents \
  -H "Content-Type: application/json" \
  -d '{"id": "zbook-test-agent", "node_id": "zbook-hp", "operator": "Claude-Code", "version": "1.0", "status": "active", "role": "tester"}'
```

### 2. Verify API Response
```bash
curl http://srv906866.hstgr.cloud:8006/api/agents
```

### 3. Open Dashboard
Navigate to: http://srv906866.hstgr.cloud:8006/

### 4. Test New Features
- Check for **REHEAT** toggle in the header (should keep mesh moving continuously)
- Check for **HEATMAP** toggle (should color nodes by activity level)

### 5. Report Findings
- Does the dashboard load with nodes?
- Do the REHEAT and HEATMAP toggles appear?
- Do they function correctly?

## Environment Info
- Feature Environment: http://srv906866.hstgr.cloud:8006/
- Production Environment: http://srv906866.hstgr.cloud:8000/
- Integration Environment: http://srv906866.hstgr.cloud:8005/
