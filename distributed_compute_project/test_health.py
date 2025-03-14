#!/usr/bin/env python3
"""
Simple test script to check the health of the head node
"""

import requests

# Head node URL
HEAD_NODE_URL = "http://localhost:5001"

def test_health():
    """Test the health check endpoint"""
    print("\n--- Testing Health Check API ---")
    try:
        response = requests.get(f"{HEAD_NODE_URL}/health", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Health check API working. Status: {status.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Failed to get health status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception when connecting to head node: {e}")
        return False

if __name__ == "__main__":
    print(f"Testing head node at {HEAD_NODE_URL}")
    test_health() 