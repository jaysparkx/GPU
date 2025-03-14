#!/usr/bin/env python3

# This script adds Ray client server support to the head node
import ray
import ray.util.client.server as ray_server
import logging
import os
import socket
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get public IP for external access
def get_public_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return socket.gethostbyname(socket.gethostname())

# Only run this if Ray is already initialized
if ray.is_initialized():
    # Start Ray Client server on port 10001
    client_server_port = 10001
    client_server_address = "0.0.0.0"
    
    # Start the Ray client server
    try:
        # Use the correct Ray 2.3.1 API to start the client server
        ray_server.serve("0.0.0.0:10001")
        logger.info(f"Ray client server running at ray://{get_public_ip()}:{client_server_port}")
    except Exception as e:
        logger.error(f"Failed to start Ray client server: {e}")
else:
    logger.error("Ray is not initialized. Cannot start Ray client server.") 