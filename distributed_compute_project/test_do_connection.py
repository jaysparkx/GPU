#!/usr/bin/env python3
import requests
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Digital Ocean server information
SERVER_IP = "143.110.246.120"
API_PORT = 5001
DASHBOARD_PORT = 8265

def test_server_health():
    """Test the health endpoint of the Digital Ocean server."""
    url = f"http://{SERVER_IP}:{API_PORT}/health"
    logger.info(f"Testing health endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logger.info(f"Server is healthy! Response: {response.json()}")
            return True
        else:
            logger.error(f"Health check failed with status code {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error: Could not connect to {url}")
        return False
    except Exception as e:
        logger.error(f"Error connecting to server: {e}")
        return False

def test_cluster_status():
    """Test the cluster status endpoint of the Digital Ocean server."""
    url = f"http://{SERVER_IP}:{API_PORT}/cluster_status"
    logger.info(f"Testing cluster status endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logger.info(f"Cluster status: {response.json()}")
            return True
        else:
            logger.error(f"Cluster status check failed with status code {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error: Could not connect to {url}")
        return False
    except Exception as e:
        logger.error(f"Error connecting to server: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"Testing connection to Digital Ocean server at {SERVER_IP}")
    
    # Test server health
    health_success = test_server_health()
    
    if health_success:
        # Test cluster status
        cluster_success = test_cluster_status()
        
        if cluster_success:
            logger.info("All tests passed! The Digital Ocean server is up and running.")
        else:
            logger.warning("The server is running but there might be issues with the Ray cluster.")
    else:
        logger.error("Failed to connect to the Digital Ocean server.")
        logger.info("Make sure the server is running and the ports are correctly exposed.")
        logger.info(f"Check the dashboard at: http://{SERVER_IP}:{DASHBOARD_PORT}") 