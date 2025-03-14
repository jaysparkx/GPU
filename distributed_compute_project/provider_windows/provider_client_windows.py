import ray
import psutil
import logging
import sys
import time
import platform
import torch
import redis
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis connection info (from environment or defaults)
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
HEAD_NODE = os.environ.get("HEAD_NODE", "head_node")

# Ensure this runs only on Windows
if platform.system() != "Windows":
    logging.error("This provider is designed for Windows only")
    sys.exit(1)

def get_capabilities():
    gpu_type = "cuda" if torch.cuda.is_available() else "cpu"
    return {
        "cpu_count": psutil.cpu_count(),
        "memory": psutil.virtual_memory().total / (1024 ** 3),
        "gpu": gpu_type
    }

def connect_to_ray():
    """Connect to Ray cluster."""
    try:
        # Connect to existing Ray cluster
        ray.init(
            address=f"ray://{HEAD_NODE}:10001",
            ignore_reinit_error=True,
            logging_level=logging.INFO
        )
        logger.info(f"Connected to Ray cluster at {HEAD_NODE}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Ray cluster: {e}")
        return False

def main():
    """Main loop for the provider client."""
    # Attempt to connect to Ray cluster
    if not connect_to_ray():
        logger.error("Failed to connect to Ray. Exiting.")
        return

    # Connect to Redis for coordination
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        ray.shutdown()
        return

    # Register as an available node
    node_id = ray.get_runtime_context().node_id
    r.sadd("available_nodes", node_id)
    r.hset(f"node:{node_id}", "status", "available")
    r.hset(f"node:{node_id}", "type", "windows")
    r.hset(f"node:{node_id}", "resources", str(ray.cluster_resources()))
    
    logger.info(f"Registered node {node_id} with the cluster")

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
                r.hset(f"node:{node_id}", "type", "windows")
            
            time.sleep(60)  # Heartbeat interval
    except KeyboardInterrupt:
        logger.info("Shutting down provider client")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        r.srem("available_nodes", node_id)
        r.delete(f"node:{node_id}")
        ray.shutdown()
        logger.info("Provider client shutdown complete")

if __name__ == "__main__":
    main() 