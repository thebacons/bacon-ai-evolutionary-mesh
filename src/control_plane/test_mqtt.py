#!/usr/bin/env python3
"""
Test script for BACON MQTT MCP Server

This script tests:
1. MQTT broker connectivity
2. Publish/subscribe functionality
3. Message round-trip

Usage:
    python test_mqtt.py [--broker BROKER] [--port PORT]
    
    # Quick test
    python test_mqtt.py
    
    # With custom broker
    python test_mqtt.py --broker localhost --port 1883
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone

# Default configuration
DEFAULT_BROKER = "srv906866.hstgr.cloud"
DEFAULT_PORT = 1883
TEST_TOPIC = "bacon/claude/test/inbox"


async def test_connectivity(broker: str, port: int) -> bool:
    """Test basic MQTT connectivity."""
    print(f"\n🔌 Testing connectivity to {broker}:{port}...")
    
    try:
        import aiomqtt
    except ImportError:
        print("❌ aiomqtt not installed. Run: pip install aiomqtt")
        return False
    
    try:
        async with aiomqtt.Client(hostname=broker, port=port) as client:
            print(f"✅ Connected to MQTT broker")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_pubsub(broker: str, port: int) -> bool:
    """Test publish/subscribe functionality."""
    print(f"\n📨 Testing pub/sub on topic: {TEST_TOPIC}")
    
    try:
        import aiomqtt
    except ImportError:
        return False
    
    received = asyncio.Event()
    received_msg = {"data": None}
    
    test_payload = {
        "type": "test",
        "content": "Hello from test script!",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    async def subscriber():
        try:
            async with aiomqtt.Client(hostname=broker, port=port) as client:
                await client.subscribe(TEST_TOPIC)
                print(f"  📥 Subscribed to {TEST_TOPIC}")
                
                async for msg in client.messages:
                    received_msg["data"] = msg.payload.decode()
                    received.set()
                    return
        except Exception as e:
            print(f"  ❌ Subscriber error: {e}")
    
    async def publisher():
        await asyncio.sleep(0.5)  # Give subscriber time to connect
        try:
            async with aiomqtt.Client(hostname=broker, port=port) as client:
                await client.publish(TEST_TOPIC, json.dumps(test_payload))
                print(f"  📤 Published test message")
        except Exception as e:
            print(f"  ❌ Publisher error: {e}")
    
    # Run subscriber and publisher concurrently
    sub_task = asyncio.create_task(subscriber())
    pub_task = asyncio.create_task(publisher())
    
    try:
        await asyncio.wait_for(received.wait(), timeout=5.0)
        print(f"  ✅ Message received: {received_msg['data'][:50]}...")
        return True
    except asyncio.TimeoutError:
        print(f"  ❌ Timeout waiting for message")
        return False
    finally:
        sub_task.cancel()
        pub_task.cancel()
        try:
            await sub_task
        except asyncio.CancelledError:
            pass
        try:
            await pub_task
        except asyncio.CancelledError:
            pass


async def test_mcp_server() -> bool:
    """Test MCP server imports and basic functionality."""
    print("\n🔧 Testing MCP server module...")
    
    try:
        from bacon_mqtt_mcp.server import mcp, get_status, send_message
        print("  ✅ Module imports successful")
        
        # Test get_status
        status = await get_status()
        print(f"  ✅ get_status() returned: {status['server']} v{status['version']}")
        print(f"     Hostname: {status['hostname']}")
        print(f"     Default topic: {status['default_topic']}")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("     Make sure you've installed: pip install -e .")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_wait_with_timeout(broker: str, port: int) -> bool:
    """Test wait_for_message with short timeout."""
    print("\n⏱️  Testing wait_for_message with 3s timeout...")
    
    try:
        from bacon_mqtt_mcp.server import wait_for_message
        
        result = await wait_for_message(
            topic=f"{TEST_TOPIC}/timeout-test",
            timeout=3
        )
        
        if result["status"] == "timeout":
            print(f"  ✅ Correctly timed out after {result['elapsed_seconds']}s")
            return True
        else:
            print(f"  ⚠️  Unexpected status: {result['status']}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_send_receive(broker: str, port: int) -> bool:
    """Test full send/receive cycle using MCP tools."""
    print("\n🔄 Testing send_message + wait_for_message cycle...")
    
    try:
        from bacon_mqtt_mcp.server import send_message, wait_for_message
        
        test_topic = f"{TEST_TOPIC}/cycle-test"
        test_content = f"Test message at {datetime.now(timezone.utc).isoformat()}"
        
        # Start listener
        async def listener():
            return await wait_for_message(topic=test_topic, timeout=10)
        
        # Send after short delay
        async def sender():
            await asyncio.sleep(1)
            return await send_message(
                message=test_content,
                topic=test_topic,
                message_type="test"
            )
        
        listener_task = asyncio.create_task(listener())
        sender_task = asyncio.create_task(sender())
        
        # Wait for both
        send_result = await sender_task
        receive_result = await listener_task
        
        if send_result["status"] == "sent" and receive_result["status"] == "received":
            print(f"  ✅ Send successful: {send_result['topic']}")
            print(f"  ✅ Receive successful: got message in {receive_result['elapsed_seconds']}s")
            
            # Verify content
            if isinstance(receive_result["message"], dict):
                if receive_result["message"].get("content") == test_content:
                    print(f"  ✅ Content verified!")
                    return True
            
            print(f"  ⚠️  Content mismatch")
            return False
        else:
            print(f"  ❌ Send status: {send_result['status']}")
            print(f"  ❌ Receive status: {receive_result['status']}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test BACON MQTT MCP Server")
    parser.add_argument("--broker", default=DEFAULT_BROKER, help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="MQTT broker port")
    parser.add_argument("--quick", action="store_true", help="Quick connectivity test only")
    args = parser.parse_args()
    
    print("=" * 60)
    print("BACON MQTT MCP Server - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Connectivity
    results.append(("Connectivity", await test_connectivity(args.broker, args.port)))
    
    if not results[-1][1]:
        print("\n❌ Connectivity failed. Cannot continue.")
        sys.exit(1)
    
    if args.quick:
        print("\n✅ Quick test passed!")
        sys.exit(0)
    
    # Test 2: Pub/Sub
    results.append(("Pub/Sub", await test_pubsub(args.broker, args.port)))
    
    # Test 3: MCP Server
    results.append(("MCP Server", await test_mcp_server()))
    
    # Test 4: Wait timeout
    results.append(("Wait Timeout", await test_wait_with_timeout(args.broker, args.port)))
    
    # Test 5: Send/Receive cycle
    results.append(("Send/Receive", await test_send_receive(args.broker, args.port)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
