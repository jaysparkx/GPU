#!/usr/bin/env python3
import ray
import requests
import socket
import time
import logging
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test provider connectivity to Ray head node')
parser.add_argument('--server', type=str, default='143.110.246.120',
                   help='Digital Ocean server IP (default: 143.110.246.120)')
parser.add_argument('--api-port', type=int, default=5001,
                   help='Head node API port (default: 5001)')
parser.add_argument('--ray-port', type=int, default=10001,
                   help='Ray client server port (default: 10001)')
args = parser.parse_args()

# Configuration
HEAD_NODE_URL = f"http://{args.server}:{args.api_port}"
RAY_ADDRESS = f"ray://{args.server}:{args.ray_port}"

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

def check_ray_port():
    """Check if the Ray client server port is open."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((args.server, args.ray_port))
        s.close()
        
        if result == 0:
            logger.info(f"Ray client port {args.ray_port} is open")
            return True
        else:
            logger.error(f"Ray client port {args.ray_port} is closed")
            return False
    except Exception as e:
        logger.error(f"Error checking Ray port: {e}")
        return False

def test_ray_connection():
    """Test connection to Ray cluster."""
    try:
        logger.info(f"Connecting to Ray at {RAY_ADDRESS}")
        ray.init(address=RAY_ADDRESS, ignore_reinit_error=True)
        
        # Define a simple remote function
        @ray.remote
        def hello():
            import platform
            return {
                "message": "Hello from provider!",
                "hostname": socket.gethostname(),
                "platform": platform.platform()
            }
        
        # Execute the remote function
        result = ray.get(hello.remote())
        logger.info(f"Ray task result: {result}")
        
        # Check available resources
        resources = ray.cluster_resources()
        logger.info(f"Cluster resources: {resources}")
        
        # Shutdown ray
        ray.shutdown()
        logger.info("Ray connection test successful!")
        return True
    except Exception as e:
        logger.error(f"Ray connection failed: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"Testing connection to Ray head node at {args.server}")
    
    # Step 1: Check if the API is reachable
    if not check_health():
        logger.error("Head node health check failed. Please ensure the server is running.")
        sys.exit(1)
    
    # Step 2: Check if the Ray port is open
    if not check_ray_port():
        logger.error("Ray client port is not accessible. Please check firewall settings.")
        sys.exit(1)
    
    # Step 3: Test Ray connection
    if test_ray_connection():
        logger.info("All tests passed! Provider can connect to the Ray cluster successfully.")
        sys.exit(0)
    else:
        logger.error("Failed to connect to Ray. Please check the configuration.")
        sys.exit(1) 