#!/bin/bash

# This script deploys the head node to Digital Ocean
set -e

# Set the Digital Ocean IP directly
export DO_SERVER_IP=143.110.246.120
echo "Server IP: $DO_SERVER_IP"

# Create log directory
mkdir -p logs

# Pull latest changes if this is a git repository
if [ -d .git ]; then
  git pull
fi

# Build and start services
docker-compose -f docker-compose.cloud.yml down --remove-orphans
docker-compose -f docker-compose.cloud.yml build --no-cache
docker-compose -f docker-compose.cloud.yml up -d

echo "Deployment completed successfully!"
echo "Head node is running at http://$DO_SERVER_IP:5001"
echo "Ray dashboard is running at http://$DO_SERVER_IP:8265"

# Display service logs
docker-compose -f docker-compose.cloud.yml logs -f 