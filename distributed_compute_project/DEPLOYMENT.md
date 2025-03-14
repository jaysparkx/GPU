# Deployment Guide

This guide provides detailed instructions for deploying and using the distributed compute project.

## Prerequisites

- **Docker and Docker Compose** - Required for all components
- **NVIDIA Container Toolkit** - Required for Windows providers with NVIDIA GPUs
- **Apple Silicon Mac (M1/M2)** - For Mac providers with MPS acceleration
- **Python 3.9+** - For running the user client and test scripts

## Deployment Options

### 1. Local Testing (Single Machine)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/distributed_compute_project.git
   cd distributed_compute_project
   ```

2. **Start the cluster with Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```

3. **Verify the cluster is running:**
   ```bash
   docker ps
   ```
   You should see containers for `redis`, `head-node`, and `provider-mac` running.

4. **Test the cluster:**
   ```bash
   python test_cluster.py
   ```

### 2. Multi-Machine Deployment

#### Head Node Setup (Main Server)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/distributed_compute_project.git
   cd distributed_compute_project
   ```

2. **Start the head node and Redis:**
   ```bash
   docker-compose up -d redis head-node
   ```

3. **Get the public IP of your head node:**
   ```bash
   PUBLIC_IP=$(curl -s ifconfig.me)
   echo "Head node available at: $PUBLIC_IP:5001"
   ```

4. **Open required ports in your firewall:**
   - 5001 (Flask API)
   - 6379 (Redis)

#### Provider Setup (Worker Machines)

##### Mac Provider (Apple Silicon)

1. **Pull the provider image:**
   ```bash
   docker pull yourdockerhubusername/provider_client_mac:latest
   ```

2. **Run the provider, connecting to the head node:**
   ```bash
   docker run -d --name provider_mac \
     -e RAY_REDIS_ADDRESS=<HEAD_NODE_IP>:6379 \
     yourdockerhubusername/provider_client_mac:latest \
     python provider_client_mac.py <HEAD_NODE_IP>:6379
   ```

##### Windows Provider (with NVIDIA GPU)

1. **Install NVIDIA Container Toolkit:**
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

2. **Pull the provider image:**
   ```bash
   docker pull yourdockerhubusername/provider_client_windows:latest
   ```

3. **Run the provider with GPU access:**
   ```bash
   docker run --gpus all -d --name provider_windows \
     -e RAY_REDIS_ADDRESS=<HEAD_NODE_IP>:6379 \
     yourdockerhubusername/provider_client_windows:latest \
     python provider_client_windows.py <HEAD_NODE_IP>:6379
   ```

### 3. Cloud Deployment (AWS/GCP/Azure)

1. **Launch instances:**
   - Head node: General-purpose instance (e.g., t3.large)
   - Mac provider: Mac instance in AWS EC2 Mac (M1)
   - Windows provider: GPU instance (e.g., p3.2xlarge with NVIDIA V100)

2. **Set up security groups/firewall rules** to allow:
   - TCP 5001 (API)
   - TCP 6379 (Redis)
   - TCP 22 (SSH)

3. **Follow the Multi-Machine Deployment steps** above, using the public IPs of your cloud instances.

## Using the Client

### Jupyter Notebook Client

1. **Install requirements:**
   ```bash
   pip install -r user_client/requirements.txt
   pip install jupyter
   ```

2. **Start Jupyter:**
   ```bash
   jupyter notebook
   ```

3. **Open the notebook:**
   - Navigate to `user_client/user_client_notebook.ipynb`
   - Update the `HEAD_NODE_URL` to your head node's address
   - Run the cells to interact with the cluster

### Command-Line Testing

1. **Test cluster status:**
   ```bash
   python test_cluster.py --url http://<HEAD_NODE_IP>:5001
   ```

2. **Test with multiple nodes:**
   ```bash
   python test_cluster.py --url http://<HEAD_NODE_IP>:5001 --nodes 2
   ```

## Monitoring and Maintenance

### Viewing Logs

```bash
# Head node logs
docker logs distributed_compute_project-head-node-1

# Provider logs
docker logs distributed_compute_project-provider-mac-1
docker logs distributed_compute_project-provider-windows-1

# Redis logs
docker logs distributed_compute_project-redis-1
```

### Restarting Services

```bash
# Restart everything
docker-compose down
docker-compose up -d

# Restart just the head node
docker-compose restart head-node
```

## Troubleshooting

1. **Connection refused errors:**
   - Check that all containers are running: `docker ps`
   - Verify network connectivity: `docker network inspect distributed_compute_project_ray-network`
   - Ensure ports are open: `netstat -tulpn | grep -E '5001|6379'`

2. **Ray initialization errors:**
   - Check Redis connection: `docker exec -it distributed_compute_project-redis-1 redis-cli ping`
   - Verify Ray is installed correctly: `docker exec -it distributed_compute_project-head-node-1 python -c "import ray; print(ray.__version__)"`

3. **GPU not detected:**
   - For Windows providers: `docker exec -it distributed_compute_project-provider-windows-1 python -c "import torch; print(torch.cuda.is_available())"`
   - For Mac providers: `docker exec -it distributed_compute_project-provider-mac-1 python -c "import torch; print(torch.backends.mps.is_available())"`

## Performance Tuning

1. **Increase Redis memory:**
   - Edit `docker-compose.yml` and update `redis` service:
     ```yaml
     command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru
     ```

2. **Increase Ray object store size:**
   - Edit `head_node/head_node.py` and update:
     ```python
     ray.init(
         address='auto',
         ignore_reinit_error=True,
         object_store_memory=10000000000,  # 10GB
     )
     ```

3. **Optimize network transfer:**
   - Use placement groups (already implemented)
   - Consider using Ray data for larger datasets

## Security Considerations

1. **Redis Authentication:**
   - Add password to Redis in `docker-compose.yml`:
     ```yaml
     command: redis-server --requirepass your_strong_password --maxmemory 2gb
     ```
   - Update Ray initialization in `head_node.py`:
     ```python
     ray.init(address=f"redis://:{os.environ.get('REDIS_PASSWORD')}@redis:6379")
     ```

2. **API Authentication:**
   - Add JWT or API key auth to the Flask API

3. **Network Security:**
   - Use VPN or private network for production deployments
   - Set up TLS/SSL for API communication 