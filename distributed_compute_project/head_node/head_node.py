from flask import Flask, request, jsonify
import ray
import numpy as np
import time
import logging
import redis
from threading import Lock
import os
from ray.util import placement_group
import torch
import socket
import requests

app = Flask(__name__)

# Logging setup with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("head_node.log")
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
SERVER_IP = os.environ.get("SERVER_IP", "0.0.0.0")  # Will be set to DO server IP

# Global state
active_tasks = {}  # {task_id: {"futures": [], "type": "", "num_nodes": 0, "pg": None}}
state_lock = Lock()

# Get public IP for external access
def get_public_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return socket.gethostbyname(socket.gethostname())

# Initialize Ray head node
try:
    # Start Ray as a head node
    ray.init(
        _node_ip_address="0.0.0.0",  # Bind to all interfaces
        include_dashboard=True,
        dashboard_host="0.0.0.0",
        ignore_reinit_error=True,
        num_cpus=os.cpu_count(),
        redis_password=os.environ.get("RAY_REDIS_PASSWORD", "5241590000000000"),
        num_gpus=0  # Cloud servers typically don't have GPUs unless specifically provisioned
    )
    logger.info(f"Ray head node initialized. Dashboard at http://localhost:8265")
    logger.info(f"Public IP for connection: {get_public_ip()}")
    logger.info(f"Available resources: {ray.cluster_resources()}")
except Exception as e:
    logger.error(f"Failed to initialize Ray: {e}")
    exit(1)

# Ray remote functions with fault tolerance and resource awareness
@ray.remote(num_cpus=1, max_retries=5)
def matrix_multiply(chunk_a, chunk_b):
    try:
        result = np.dot(chunk_a, chunk_b)
        return result
    except Exception as e:
        logger.error(f"Matrix multiplication failed: {e}")
        raise

@ray.remote(num_cpus=1, max_retries=5)
def train_pytorch(chunk_inputs, chunk_targets):
    import torch
    import torch.nn as nn
    from torch.optim import SGD

    try:
        device = torch.device("cpu")  # Use CPU on server
        model = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        ).to(device)
        
        inputs = torch.tensor(chunk_inputs).to(device)
        targets = torch.tensor(chunk_targets).long().to(device)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = SGD(model.parameters(), lr=0.01)
        
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        
        gradients = {name: param.grad.cpu().numpy().tolist() for name, param in model.named_parameters() if param.grad is not None}
        return gradients
    except Exception as e:
        logger.error(f"PyTorch training failed: {e}")
        raise

# API: Submit a task
@app.route('/submit_task', methods=['POST'])
def submit_task():
    try:
        data = request.json
        task_id = str(int(time.time() * 1000))
        task_type = data["type"]
        num_nodes = data.get("num_nodes", 0)  # Default to 0 nodes (use head node)
        user_id = data.get("user_id", "user_1")
        matrix_size = data.get("size", 1000)  # Default to 1000, but allow smaller sizes

        with state_lock:
            available_nodes = len([n for n in ray.nodes() if n["Alive"]]) - 1  # Exclude head node
            if num_nodes > available_nodes:
                return jsonify({"status": "error", "message": f"Requested {num_nodes} nodes, only {available_nodes} available"})

            # Create a placement group for task distribution
            # If num_nodes is 0, use the head node (1 bundle)
            actual_nodes = max(1, num_nodes)  # Ensure at least 1 node
            pg = placement_group([{"CPU": 1}] * actual_nodes, strategy="SPREAD")
            ray.get(pg.ready())

            if task_type == "matrix_mult":
                matrix_a = np.random.rand(matrix_size, matrix_size)
                matrix_b = np.random.rand(matrix_size, matrix_size)
                chunk_size = matrix_size // actual_nodes
                futures = []
                for i in range(0, matrix_size, chunk_size):
                    chunk_a = matrix_a[i:i+chunk_size, :]
                    futures.append(matrix_multiply.options(placement_group=pg).remote(chunk_a, matrix_b))
            elif task_type == "pytorch_train":
                inputs = np.random.randn(1000, 784)
                targets = np.random.randint(0, 10, (1000,))
                chunk_size = 1000 // actual_nodes
                futures = []
                for i in range(0, 1000, chunk_size):
                    chunk_inputs = inputs[i:i+chunk_size].tolist()
                    chunk_targets = targets[i:i+chunk_size].tolist()
                    futures.append(train_pytorch.options(placement_group=pg).remote(chunk_inputs, chunk_targets))
            else:
                return jsonify({"status": "error", "message": "Invalid task type"})

            active_tasks[task_id] = {"futures": futures, "type": task_type, "num_nodes": num_nodes, "pg": pg}
            logger.info(f"Task {task_id} submitted with {num_nodes} nodes")

        return jsonify({"status": "success", "task_id": task_id})
    except Exception as e:
        logger.error(f"Error in submit_task: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API: Check task status
@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    try:
        with state_lock:
            if task_id not in active_tasks:
                return jsonify({"status": "error", "message": "Task not found"})
            
            task = active_tasks[task_id]
            try:
                # Increase timeout for remote connections
                results = ray.get(task["futures"], timeout=600)
                if task["type"] == "matrix_mult":
                    result = np.vstack(results)
                    ray.util.remove_placement_group(task["pg"])
                    del active_tasks[task_id]
                    # Return dimensions instead of full matrix to save bandwidth
                    return jsonify({
                        "status": "completed", 
                        "dimensions": result.shape,
                        "sample": result[:5, :5].tolist()  # Just return a sample
                    })
                elif task["type"] == "pytorch_train":
                    aggregated_grads = {}
                    for grad_dict in results:
                        for name, grad in grad_dict.items():
                            if name not in aggregated_grads:
                                aggregated_grads[name] = np.array(grad)
                            else:
                                aggregated_grads[name] += np.array(grad)
                    for name in aggregated_grads:
                        aggregated_grads[name] = (aggregated_grads[name] / len(results)).tolist()
                    ray.util.remove_placement_group(task["pg"])
                    del active_tasks[task_id]
                    return jsonify({"status": "completed", "results": "Gradients computed successfully"})
            except ray.exceptions.RayTaskError as e:
                logger.error(f"Task {task_id} failed: {e}")
                ray.util.remove_placement_group(task["pg"])
                del active_tasks[task_id]
                return jsonify({"status": "failed", "message": str(e)})
            except ray.exceptions.TaskTimeoutError:
                logger.warning(f"Task {task_id} still running")
                return jsonify({"status": "pending", "message": "Task still running"})
    except Exception as e:
        logger.error(f"Error in task_status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API: Cluster status
@app.route('/cluster_status', methods=['GET'])
def cluster_status():
    try:
        nodes = ray.nodes()
        alive_nodes = [n for n in nodes if n["Alive"]]
        detailed_nodes = []
        
        for node in alive_nodes:
            detailed_nodes.append({
                "node_id": node["NodeID"],
                "address": node["NodeManagerAddress"],
                "resources": node["Resources"],
                "alive": node["Alive"]
            })
        
        return jsonify({
            "status": "success",
            "num_nodes": len(alive_nodes) - 1,  # Exclude head node
            "resources": ray.cluster_resources(),
            "nodes": detailed_nodes
        })
    except Exception as e:
        logger.error(f"Error in cluster_status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API: Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "version": "1.0", "ray_status": "connected" if ray.is_initialized() else "disconnected"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True) 