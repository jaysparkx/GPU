#!/usr/bin/env python3
"""
Test script to verify the head node API functionality
"""

import requests
import time
import json

# Head node URL
HEAD_NODE_URL = "http://localhost:5001"

def test_cluster_status():
    """Test the cluster status API endpoint"""
    print("\n--- Testing Cluster Status API ---")
    try:
        response = requests.get(f"{HEAD_NODE_URL}/cluster_status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Cluster status API working. Found {status['num_nodes']} worker nodes")
            print(f"  Resources: {json.dumps(status['resources'], indent=2)}")
            return True
        else:
            print(f"❌ Failed to get cluster status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception when connecting to cluster: {e}")
        return False

def test_matrix_task(num_nodes=0):
    """Test matrix multiplication task submission and status"""
    print(f"\n--- Testing Matrix Multiplication with {num_nodes} nodes ---")
    try:
        # Submit task
        response = requests.post(
            f"{HEAD_NODE_URL}/submit_task", 
            json={"type": "matrix_mult", "num_nodes": num_nodes},
            timeout=30  # Increased timeout
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
        max_attempts = 20  # Increased max attempts
        for i in range(max_attempts):
            print(f"  Checking task status (attempt {i+1}/{max_attempts})...")
            status_response = requests.get(f"{HEAD_NODE_URL}/task_status/{task_id}", timeout=30)  # Increased timeout
            
            if status_response.status_code != 200:
                print(f"❌ Failed to get task status: {status_response.status_code}")
                time.sleep(5)  # Increased sleep time
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
                time.sleep(5)  # Increased sleep time
            else:
                print(f"  Unexpected status: {status_result}")
                time.sleep(5)  # Increased sleep time
        
        print("❌ Timed out waiting for task completion")
        return False
    
    except Exception as e:
        print(f"❌ Exception during matrix task test: {e}")
        return False

def main():
    print(f"Testing cluster at {HEAD_NODE_URL}")
    
    # Test cluster status
    if not test_cluster_status():
        print("\n❌ Cluster status test failed. Exiting.")
        return
    
    # Test matrix multiplication task
    if not test_matrix_task(num_nodes=0):
        print("\n❌ Matrix task test failed. Exiting.")
        return
    
    print("\n✅ All tests passed successfully!")

if __name__ == "__main__":
    main() 