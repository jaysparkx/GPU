import ray
import psutil
import logging
import sys
import time
import platform
import torch
import os
import redis
import numpy as np
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("provider_mac.log")
    ]
)
logger = logging.getLogger(__name__)

# Server connection info - update this with your DO server IP
DO_SERVER_IP = os.environ.get("DO_SERVER_IP", "YOUR_DIGITAL_OCEAN_IP")
REDIS_HOST = os.environ.get("REDIS_HOST", DO_SERVER_IP)
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
HEAD_NODE = os.environ.get("HEAD_NODE", DO_SERVER_IP)
RAY_REDIS_PASSWORD = os.environ.get("RAY_REDIS_PASSWORD", "5241590000000000")

# Ensure this runs only on Mac or if DOCKER_ENV is set
if platform.system() != "Darwin" and not os.environ.get("DOCKER_ENV"):
    logging.error("This provider is designed for macOS only")
    sys.exit(1)

def get_capabilities():
    gpu_type = "mps" if torch.backends.mps.is_available() else "cpu"
    return {
        "cpu_count": psutil.cpu_count(),
        "memory": psutil.virtual_memory().total / (1024 ** 3),
        "gpu": gpu_type
    }

def check_server_health():
    """Check if the head node server is healthy"""
    try:
        response = requests.get(f"http://{HEAD_NODE}:5001/health", timeout=10)
        if response.status_code == 200:
            logger.info(f"Head node health check: {response.json()}")
            return True
        else:
            logger.error(f"Head node health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Cannot connect to head node: {e}")
        return False

def run_simple_task():
    """Run a simple Ray task to verify connectivity."""
    @ray.remote
    def simple_task():
        return "Hello from Mac provider node!"
    
    try:
        result = ray.get(simple_task.remote())
        logger.info(f"Simple task result: {result}")
        return True
    except Exception as e:
        logger.error(f"Failed to run simple task: {e}")
        return False

def connect_to_ray():
    """Connect to Ray cluster."""
    try:
        # First check if the server is up
        if not check_server_health():
            logger.error("Head node is not healthy")
            return False
            
        # Connect to existing Ray cluster
        ray.init(
            address=f"{HEAD_NODE}:6379",
            _redis_password=RAY_REDIS_PASSWORD,
            ignore_reinit_error=True,
            logging_level=logging.INFO
        )
        logger.info(f"Connected to Ray cluster at {HEAD_NODE}")
        
        # Run a simple task to verify connectivity
        if run_simple_task():
            return True
        else:
            logger.error("Connected to Ray but failed to run a simple task")
            ray.shutdown()
            return False
    except Exception as e:
        logger.error(f"Failed to connect to Ray cluster: {e}")
        return False

def main():
    """Main loop for the provider client."""
    logger.info(f"Starting Mac provider client, connecting to {HEAD_NODE}")
    logger.info(f"System capabilities: {get_capabilities()}")
    
    # Attempt to connect to Ray cluster
    retry_count = 0
    max_retries = 10  # More retries for remote connection
    
    while retry_count < max_retries:
        if connect_to_ray():
            logger.info("Successfully connected to Ray cluster")
            break
        else:
            retry_count += 1
            wait_time = min(30, 5 * retry_count)  # Progressive backoff
            logger.warning(f"Failed to connect to Ray cluster. Retry {retry_count}/{max_retries} in {wait_time}s")
            time.sleep(wait_time)  # Wait before retrying
    
    if retry_count == max_retries:
        logger.error("Failed to connect to Ray after maximum retries. Exiting.")
        return

    # Connect to Redis for coordination
    try:
        r = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=0,
            socket_timeout=10
        )
        r.ping()  # Test connection
        logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        ray.shutdown()
        return

    # Register as an available node
    node_id = ray.get_runtime_context().node_id
    r.sadd("available_nodes", node_id)
    r.hset(f"node:{node_id}", "status", "available")
    r.hset(f"node:{node_id}", "type", "mac")
    r.hset(f"node:{node_id}", "resources", str(ray.cluster_resources()))
    r.hset(f"node:{node_id}", "capabilities", str(get_capabilities()))
    
    logger.info(f"Registered node {node_id} with the cluster")
    logger.info("Mac provider is now active and ready to process tasks")

    try:
        # Main loop - keep running to provide resources to the cluster
        while True:
            # Keep the connection alive
            if r.exists(f"node:{node_id}"):
                r.hset(f"node:{node_id}", "last_seen", int(time.time()))
                logger.info(f"Node {node_id} still active")
            else:
                logger.warning("Node record not found, re-registering")
                r.sadd("available_nodes", node_id)
                r.hset(f"node:{node_id}", "status", "available")
                r.hset(f"node:{node_id}", "type", "mac")
                r.hset(f"node:{node_id}", "capabilities", str(get_capabilities()))
            
            # Run a simple task periodically to verify Ray connectivity
            if not run_simple_task():
                logger.warning("Ray connection may be unstable, attempting to reconnect...")
                ray.shutdown()
                if not connect_to_ray():
                    logger.error("Failed to reconnect to Ray cluster")
                    break
            
            time.sleep(60)  # Heartbeat interval
    except KeyboardInterrupt:
        logger.info("Shutting down provider client")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        try:
            r.srem("available_nodes", node_id)
            r.delete(f"node:{node_id}")
        except:
            pass
        ray.shutdown()
        logger.info("Provider client shutdown complete")

if __name__ == "__main__":
    main() 