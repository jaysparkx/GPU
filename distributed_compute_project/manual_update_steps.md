# Manual Update Steps for Digital Ocean Head Node

Follow these steps to update the head node on your Digital Ocean server and enable Ray client server support for provider connections.

## Step 1: Update head_node.py on Digital Ocean

SSH into your Digital Ocean server:

```bash
ssh root@143.110.246.120
```

Edit the head_node.py file:

```bash
cd ~/GPU/distributed_compute_project/head_node
nano head_node.py
```

Add the following import at the top of the file with the other imports:

```python
import ray.util.client.server as ray_server
```

Add the following code after Ray initialization (after the "Available resources" log):

```python
# Start Ray Client server on port 10001
client_server_port = 10001
client_server_address = "0.0.0.0"
    
# Start the Ray client server using the correct API for Ray 2.3.1
ray_server.serve("0.0.0.0:10001")
logger.info(f"Ray client server running at ray://{get_public_ip()}:{client_server_port}")
```

Save the file and exit (Ctrl+X, then Y, then Enter).

## Step 2: Open port 10001 on the Digital Ocean firewall

```bash
# Check current firewall status
ufw status

# Allow Ray client server port
ufw allow 10001/tcp

# Verify the change
ufw status
```

## Step 3: Restart the services

```bash
cd ~/GPU/distributed_compute_project
docker-compose -f docker-compose.cloud.yml down
docker-compose -f docker-compose.cloud.yml up -d --build
```

## Step 4: Verify that the services are running

```bash
docker-compose -f docker-compose.cloud.yml logs -f head-node
```

You should see log messages indicating that the Ray client server is running.

## Step 5: Test from your local Mac

Back on your local Mac, run the provider test:

```bash
cd ~/Documents/GPU/distributed_compute_project
python3 provider_test.py
```

If everything is set up correctly, you should see a successful connection to the Ray head node.

## Step 6: Run the provider client

```bash
docker-compose -f docker-compose.provider.yml up --build
```

You should see the provider connect to the Ray cluster and register with the Redis server. 