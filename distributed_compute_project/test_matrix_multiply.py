#!/usr/bin/env python3
import requests
import json
import time
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test matrix multiplication on Ray cluster')
parser.add_argument('--server', type=str, default='143.110.246.120',
                   help='Digital Ocean server IP (default: 143.110.246.120)')
parser.add_argument('--port', type=int, default=5001,
                   help='Head node port (default: 5001)')
parser.add_argument('--size', type=int, default=100,
                   help='Matrix size (default: 100)')
args = parser.parse_args()

# Configuration
HEAD_NODE_URL = f"http://{args.server}:{args.port}"
MATRIX_SIZE = args.size

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
            return cluster_status
        else:
            logger.error(f"Failed to get cluster status: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error checking cluster status: {e}")
        return None

def test_matrix_multiplication():
    """Test matrix multiplication task on the cluster."""
    logger.info(f"Testing matrix multiplication with {MATRIX_SIZE}x{MATRIX_SIZE} matrices")
    
    # Prepare task submission
    task_data = {
        "type": "matrix_mult",
        "size": MATRIX_SIZE
    }
    
    try:
        # Submit the task
        logger.info("Submitting matrix multiplication task...")
        submit_response = requests.post(
            f"{HEAD_NODE_URL}/submit_task", 
            json=task_data,
            timeout=30
        )
        
        if submit_response.status_code != 200:
            logger.error(f"Failed to submit task: {submit_response.text}")
            return False
        
        task_info = submit_response.json()
        if "task_id" not in task_info:
            logger.error(f"No task_id in response: {task_info}")
            return False
            
        task_id = task_info["task_id"]
        logger.info(f"Task submitted successfully with ID: {task_id}")
        
        # Poll for task completion
        max_polls = 20
        poll_interval = 5  # seconds
        for i in range(max_polls):
            logger.info(f"Checking task status (attempt {i+1}/{max_polls})...")
            status_response = requests.get(
                f"{HEAD_NODE_URL}/task_status/{task_id}",
                timeout=15
            )
            
            if status_response.status_code != 200:
                logger.error(f"Failed to get task status: {status_response.text}")
                time.sleep(poll_interval)
                continue
            
            status_info = status_response.json()
            status = status_info.get("status")
            
            if status == "completed":
                logger.info("Task completed successfully!")
                if "dimensions" in status_info:
                    logger.info(f"Result matrix dimensions: {status_info['dimensions']}")
                    logger.info(f"Sample of result: {status_info.get('sample')}")
                return True
            elif status == "failed":
                logger.error(f"Task failed: {status_info.get('message')}")
                return False
            elif status == "pending":
                logger.info("Task is still running...")
                time.sleep(poll_interval)
            else:
                logger.warning(f"Unexpected status: {status}")
                time.sleep(poll_interval)
        
        logger.error("Task timed out after maximum polling attempts")
        return False
    
    except Exception as e:
        logger.error(f"Error during matrix multiplication test: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"Testing Ray cluster at {HEAD_NODE_URL}")
    
    # First check health
    if not check_health():
        logger.error("Head node is not healthy. Exiting.")
        exit(1)
    
    # Check cluster status
    cluster_status = check_cluster_status()
    if not cluster_status:
        logger.warning("Could not get cluster status, but continuing anyway...")
    
    # Run the matrix multiplication test
    success = test_matrix_multiplication()
    
    if success:
        logger.info("Matrix multiplication test completed successfully!")
        exit(0)
    else:
        logger.error("Matrix multiplication test failed")
        exit(1) 