# Deploying to Digital Ocean

This guide explains how to deploy the head node on a Digital Ocean droplet and connect provider nodes.

## 1. Create a Digital Ocean Droplet

1. Log in to your Digital Ocean account
2. Create a new Droplet with:
   - Ubuntu 20.04 LTS
   - At least 4GB RAM
   - 2 vCPUs
   - 80GB SSD

## 2. Set up the Droplet

SSH into your new droplet:

```bash
ssh root@143.110.246.120
```

Install Docker and Docker Compose:

```bash
# Update package lists
apt update

# Install Docker
apt install -y docker.io

# Install Docker Compose
apt install -y docker-compose

# Check installations
docker --version
docker-compose --version
```

## 3. Upload project files

From your local machine:

```bash
# Clone the repo if you haven't already
git clone https://github.com/yourusername/distributed_compute_project.git

# Upload to Digital Ocean
scp -r distributed_compute_project root@143.110.246.120:~/
```

## 4. Deploy on Digital Ocean

SSH into your droplet again:

```bash
ssh root@143.110.246.120
```

Navigate to the project and deploy:

```bash
cd distributed_compute_project
chmod +x deploy_to_do.sh
./deploy_to_do.sh
```

The deployment script will:
- Detect your droplet's IP
- Build and start the containers
- Display the service logs

## 5. Connect a provider from your local machine

On your local machine:

1. Edit `docker-compose.provider.yml` to use your Digital Ocean IP:
   ```yaml
   environment:
     - DO_SERVER_IP=143.110.246.120
     - HEAD_NODE=143.110.246.120 
     - REDIS_HOST=143.110.246.120
   ```

2. Run the provider:
   ```bash
   cd distributed_compute_project
   docker-compose -f docker-compose.provider.yml up
   ```

## 6. Test the deployment

Run the test script:

```bash
cd distributed_compute_project
python test_matrix_multiply_remote.py --server 143.110.246.120
```

## Troubleshooting

1. Check if all services are running:
   ```bash
   docker-compose -f docker-compose.cloud.yml ps
   ```

2. View logs for a specific service:
   ```bash
   docker-compose -f docker-compose.cloud.yml logs head-node
   ```

3. Restart services:
   ```bash
   docker-compose -f docker-compose.cloud.yml restart
   ``` 