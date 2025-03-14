#!/usr/bin/env python3
"""
Test client for distributed compute project
This script submits tasks to the head node and retrieves the results
"""

import requests
import json
import time
import logging
import argparse
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test client for distributed compute project')
parser.add_argument('--server', type=str, default='143.110.246.120',
                   help='Digital Ocean server IP (default: 143.110.246.120)')
parser.add_argument('--port', type=int, default=5001,
                   help='Head node port (default: 5001)')
parser.add_argument('--task', choices=['matrix', 'complex'], default='matrix',
                   help='Task to submit (default: matrix)')
parser.add_argument('--size', type=int, default=500,
                   help='Matrix size for matrix task (default: 500)')
args = parser.parse_args()

# Configuration
HEAD_NODE_URL = f"http://{args.server}:{args.port}"

def check_health():
    """Check if the head node is healthy."""
    try:
        response = requests.get(f"{HEAD_NODE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_status = response.json()
            logger.info(f"Health status: {health_status}")
            return True
        else:
            logger.error(f"Health check failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to head node: {e}")
        return False

def check_cluster_status():
    """Check the status of the Ray cluster."""
    try:
        response = requests.get(f"{HEAD_NODE_URL}/cluster_status", timeout=10)
        if response.status_code == 200:
            cluster_status = response.json()
            logger.info(f"Cluster status: {json.dumps(cluster_status, indent=2)}")
            
            # Return the number of provider nodes
            nodes = cluster_status.get("nodes", [])
            logger.info(f"Number of nodes in the cluster: {len(nodes)}")
            
            return cluster_status
        else:
            logger.error(f"Failed to get cluster status: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error checking cluster status: {e}")
        return None

def submit_matrix_task(size):
    """Submit a matrix multiplication task."""
    try:
        task_data = {
            "type": "matrix_mult",
            "size": size,
            "user_id": "test_client"
        }
        
        logger.info(f"Submitting matrix multiplication task with size {size}...")
        response = requests.post(
            f"{HEAD_NODE_URL}/submit_task", 
            json=task_data,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to submit task: {response.text}")
            return None
        
        task_info = response.json()
        if "task_id" not in task_info:
            logger.error(f"No task_id in response: {task_info}")
            return None
            
        task_id = task_info["task_id"]
        logger.info(f"Task submitted successfully with ID: {task_id}")
        return task_id
    
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        return None

def submit_complex_task():
    """Submit a more complex task that combines multiple operations."""
    try:
        task_data = {
            "type": "complex",
            "operations": ["matrix_mult", "process_results"],
            "size": 200,
            "iterations": 3,
            "user_id": "test_client"
        }
        
        logger.info(f"Submitting complex task...")
        response = requests.post(
            f"{HEAD_NODE_URL}/submit_task", 
            json=task_data,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to submit task: {response.text}")
            return None
        
        task_info = response.json()
        if "task_id" not in task_info:
            logger.error(f"No task_id in response: {task_info}")
            return None
            
        task_id = task_info["task_id"]
        logger.info(f"Task submitted successfully with ID: {task_id}")
        return task_id
    
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        return None

def check_task_status(task_id, max_polls=20, poll_interval=5):
    """Check the status of a task and wait for completion."""
    for i in range(max_polls):
        try:
            logger.info(f"Checking task status (attempt {i+1}/{max_polls})...")
            response = requests.get(
                f"{HEAD_NODE_URL}/task_status/{task_id}",
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get task status: {response.text}")
                time.sleep(poll_interval)
                continue
            
            status_info = response.json()
            status = status_info.get("status")
            
            if status == "completed":
                logger.info("Task completed successfully!")
                return status_info
            elif status == "failed":
                logger.error(f"Task failed: {status_info.get('message')}")
                return status_info
            elif status == "pending":
                logger.info(f"Task is still running... (elapsed: {(i+1)*poll_interval}s)")
                time.sleep(poll_interval)
            else:
                logger.warning(f"Unexpected status: {status}")
                time.sleep(poll_interval)
        
        except Exception as e:
            logger.error(f"Error checking task status: {e}")
            time.sleep(poll_interval)
    
    logger.error("Task timed out after maximum polling attempts")
    return {"status": "timeout"}

def main():
    """Main function."""
    logger.info(f"Testing distributed compute project with head node at {HEAD_NODE_URL}")
    
    # Step 1: Check if the API is reachable
    if not check_health():
        logger.error("Head node health check failed. Please ensure the server is running.")
        sys.exit(1)
    
    # Step 2: Check cluster status
    cluster_status = check_cluster_status()
    if not cluster_status:
        logger.warning("Could not get cluster status. Continuing anyway...")
    
    # Step 3: Submit a task
    task_id = None
    if args.task == "matrix":
        task_id = submit_matrix_task(args.size)
    elif args.task == "complex":
        task_id = submit_complex_task()
    
    if not task_id:
        logger.error("Failed to submit task.")
        sys.exit(1)
    
    # Step 4: Check task status
    result = check_task_status(task_id)
    
    if result.get("status") == "completed":
        logger.info(f"Task details: {json.dumps(result, indent=2)}")
        logger.info("Client test completed successfully!")
        sys.exit(0)
    else:
        logger.error(f"Task did not complete successfully: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main() 