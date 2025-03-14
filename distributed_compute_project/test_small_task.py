#!/usr/bin/env python3
"""
Test script to submit a small matrix multiplication task
"""

import requests
import time
import json

# Head node URL
HEAD_NODE_URL = "http://localhost:5001"

def submit_small_task():
    """Submit a small matrix multiplication task"""
    print("\n--- Submitting Small Matrix Multiplication Task ---")
    try:
        # Submit task with a small matrix size
        response = requests.post(
            f"{HEAD_NODE_URL}/submit_task", 
            json={"type": "matrix_mult", "num_nodes": 0, "size": 100},  # Small matrix size
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to submit task: {response.status_code}")
            return False
        
        result = response.json()
        if result.get("status") != "success":
            print(f"❌ Task submission failed: {result}")
            return False
        
        task_id = result["task_id"]
        print(f"✅ Task submitted successfully with ID: {task_id}")
        
        # Poll for results
        max_attempts = 10
        for i in range(max_attempts):
            print(f"  Checking task status (attempt {i+1}/{max_attempts})...")
            status_response = requests.get(f"{HEAD_NODE_URL}/task_status/{task_id}", timeout=10)
            
            if status_response.status_code != 200:
                print(f"❌ Failed to get task status: {status_response.status_code}")
                time.sleep(2)
                continue
            
            status_result = status_response.json()
            if status_result.get("status") == "completed":
                print(f"✅ Task completed successfully!")
                result_preview = str(status_result["results"])[:100] + "..." if len(str(status_result["results"])) > 100 else status_result["results"]
                print(f"  Results: {result_preview}")
                return True
            elif status_result.get("status") == "failed":
                print(f"❌ Task failed: {status_result.get('message')}")
                return False
            elif status_result.get("status") == "pending":
                print(f"  Task still running...")
                time.sleep(2)
            else:
                print(f"  Unexpected status: {status_result}")
                time.sleep(2)
        
        print("❌ Timed out waiting for task completion")
        return False
    
    except Exception as e:
        print(f"❌ Exception during task test: {e}")
        return False

if __name__ == "__main__":
    print(f"Testing cluster at {HEAD_NODE_URL}")
    submit_small_task() 