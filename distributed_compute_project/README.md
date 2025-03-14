# Distributed Compute Project

A Ray-based decentralized cloud computing platform inspired by io.net, supporting platform-specific workers (Mac M1/M2 and Windows NVIDIA) with fault tolerance and dynamic scaling.

## Key Features

1. **Large Compute**: Optimized for scalability using Ray's distributed framework, supporting hundreds of nodes.
2. **Platform-Specific Workers**: Separate Mac (M1/M2 MPS) and Windows (NVIDIA CUDA/CPU) providers.
3. **Fault Tolerance**: Automatic task retry and worker replacement if a node fails.
4. **Easy Docker Setup**: Pre-built Docker containers for instant provider onboarding.
5. **Client Control**: Notebook interface to specify `num_nodes`, using a mix of available devices.
6. **Decentralized Vision**: Built with future decentralization in mind.
7. **Fixed Redis/Networking**: Explicit Redis configuration and robust Docker networking.

## Project Structure

```
distributed_compute_project/
│
├── head_node/               # Ray head node with Flask API
│   ├── head_node.py         # Main head node implementation
│   ├── Dockerfile           # Container setup
│   ├── requirements.txt     # Dependencies
│   └── README.md            # Head node documentation
│
├── provider_mac/            # Mac-specific provider (M1/M2)
│   ├── provider_client_mac.py  # Mac provider implementation
│   ├── Dockerfile              # Container setup
│   ├── requirements.txt        # Dependencies
│   └── README.md               # Mac provider documentation
│
├── provider_windows/        # Windows-specific provider (NVIDIA)  
│   ├── provider_client_windows.py  # Windows provider implementation
│   ├── Dockerfile                  # Container setup
│   ├── requirements.txt            # Dependencies 
│   └── README.md                   # Windows provider documentation
│
├── user_client/             # Client for submitting tasks
│   ├── user_client_notebook.ipynb  # Jupyter notebook for users
│   ├── requirements.txt            # Dependencies
│   └── README.md                   # User client documentation
│
├── docker-compose.yml       # Container orchestration
└── README.md                # Project documentation
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- For GPU support:
  - Mac: Apple Silicon (M1/M2) for MPS acceleration
  - Windows: NVIDIA GPU with CUDA support and NVIDIA Container Toolkit

### Running the Cluster

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/distributed_compute_project.git
   cd distributed_compute_project
   ```

2. Start the cluster:
   ```bash
   docker-compose up --build -d
   ```

3. Access the user interface:
   - Open `user_client/user_client_notebook.ipynb` in Jupyter
   - Set `HEAD_NODE_URL` to "http://localhost:5001"
   - Run the notebook cells to submit tasks

### Joining as a Provider

#### Mac Provider:
```bash
docker pull yourdockerhubusername/provider_client_mac:latest
docker run -d --name provider_client_mac yourdockerhubusername/provider_client_mac:latest
```

#### Windows Provider (with NVIDIA GPU):
```bash
docker pull yourdockerhubusername/provider_client_windows:latest
docker run --gpus all -d --name provider_client_windows yourdockerhubusername/provider_client_windows:latest
```

## Supported Task Types

1. **Matrix Multiplication**: Distributes large matrix operations across nodes
2. **PyTorch Training**: Distributes neural network training with gradient aggregation

## License

[MIT License](LICENSE)

## Acknowledgments

- Inspired by [io.net](https://docs.io.net/)
- Built with [Ray](https://ray.io/) 