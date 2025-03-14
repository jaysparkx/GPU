#!/usr/bin/env python3
import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
HEAD_NODE_URL = "http://localhost:5001"  # The exposed port from docker-compose
MATRIX_SIZE = 10  # Size of matrices to multiply (NxN)

def test_small_matrix_multiplication():
    """Test a very small matrix multiplication task on the cluster."""
    logger.info(f"Testing matrix multiplication with {MATRIX_SIZE}x{MATRIX_SIZE} matrices")
    
    # Prepare task submission
    task_data = {
        "type": "matrix_mult",
        "num_nodes": 0,  # Use the head node only
        "size": MATRIX_SIZE
    }
    
    try:
        # Submit the task
        logger.info("Submitting matrix multiplication task...")
        submit_response = requests.post(
            f"{HEAD_NODE_URL}/submit_task", 
            json=task_data,
            timeout=10
        )
        
        if submit_response.status_code != 200:
            logger.error(f"Failed to submit task: {submit_response.text}")
            return False
        
        task_info = submit_response.json()
        logger.info(f"Task submission response: {task_info}")
        
        if "task_id" not in task_info:
            logger.error(f"No task_id in response: {task_info}")
            return False
            
        task_id = task_info["task_id"]
        logger.info(f"Task submitted successfully with ID: {task_id}")
        
        # Poll for task completion
        max_polls = 10
        poll_interval = 2  # seconds
        for i in range(max_polls):
            logger.info(f"Checking task status (attempt {i+1}/{max_polls})...")
            status_response = requests.get(
                f"{HEAD_NODE_URL}/task_status/{task_id}",
                timeout=5
            )
            
            if status_response.status_code != 200:
                logger.error(f"Failed to get task status: {status_response.text}")
                time.sleep(poll_interval)
                continue
            
            status_info = status_response.json()
            status = status_info.get("status")
            
            if status == "completed":
                logger.info("Task completed successfully!")
                result_shape = len(status_info["results"])
                logger.info(f"Result is a {result_shape}x{result_shape} matrix")
                return True
            elif status == "failed":
                logger.error(f"Task failed: {status_info.get('message', 'Unknown error')}")
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
    
    # Run the matrix multiplication test
    success = test_small_matrix_multiplication()
    
    if success:
        logger.info("Matrix multiplication test completed successfully")
        exit(0)
    else:
        logger.error("Matrix multiplication test failed")
        exit(1) 