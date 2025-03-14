#!/bin/bash
# Script to update the head node on Digital Ocean with Ray client server support

# Set server IP (can be overridden by environment variable)
DO_SERVER_IP=${DO_SERVER_IP:-"143.110.246.120"}
echo "Server IP: $DO_SERVER_IP"

# Make files executable
chmod +x provider_test.py
chmod +x test_client.py

# Copy the updated head_node.py to the server
echo "Copying updated head_node.py to Digital Ocean server..."
scp -o StrictHostKeyChecking=no head_node/head_node.py root@${DO_SERVER_IP}:~/GPU/distributed_compute_project/head_node/

# Rebuild and restart the services on the Digital Ocean server
echo "Rebuilding and restarting services on Digital Ocean..."
ssh -o StrictHostKeyChecking=no root@${DO_SERVER_IP} "cd ~/GPU/distributed_compute_project && docker-compose -f docker-compose.cloud.yml down && docker-compose -f docker-compose.cloud.yml up -d --build"

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Open port 10001 on the Digital Ocean server
echo "Configuring firewall to allow Ray client server port..."
ssh -o StrictHostKeyChecking=no root@${DO_SERVER_IP} "ufw allow 10001/tcp && ufw status"

# Wait a bit more for the Ray client server to start
echo "Waiting for Ray client server to initialize..."
sleep 10

# Test the connection to the Ray head node
echo "Testing connection to Ray head node..."
./provider_test.py --server $DO_SERVER_IP

echo "Update completed!" 