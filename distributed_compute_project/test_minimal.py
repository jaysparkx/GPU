#!/usr/bin/env python3
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
HEAD_NODE_URL = "http://localhost:5001"  # The exposed port from docker-compose

def test_cluster_status():
    """Test the cluster status endpoint of the head node."""
    logger.info(f"Testing cluster status endpoint at {HEAD_NODE_URL}/cluster_status")
    
    try:
        response = requests.get(f"{HEAD_NODE_URL}/cluster_status", timeout=5)
        if response.status_code == 200:
            cluster_status = response.json()
            logger.info(f"Cluster status: {json.dumps(cluster_status, indent=2)}")
            return True
        else:
            logger.error(f"Cluster status check failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Cluster status check error: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"Testing Ray cluster at {HEAD_NODE_URL}")
    
    # Run the cluster status check
    success = test_cluster_status()
    
    if success:
        logger.info("Cluster status check completed successfully")
        exit(0)
    else:
        logger.error("Cluster status check failed")
        exit(1) 