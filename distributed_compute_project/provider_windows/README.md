# Windows Provider Client Setup

## Prerequisites
- Docker installed (Docker Desktop on Windows)
- Windows system (will not run on macOS)
- Optional: NVIDIA Container Toolkit for GPU support

## Steps to Join as a Worker
1. **Pull Docker Image**:
   ```bash
   docker pull yourdockerhubusername/provider_client_windows:latest
   ```
   (Replace `yourdockerhubusername` with the actual Docker Hub username after publishing.)

2. **Run Docker Container**:
   - With GPU:
     ```bash
     docker run --gpus all -d --name provider_client_windows yourdockerhubusername/provider_client_windows:latest
     ```
   - Without GPU:
     ```bash
     docker run -d --name provider_client_windows yourdockerhubusername/provider_client_windows:latest
     ```

## Notes
- Designed for Windows with NVIDIA GPU (CUDA) or CPU (e.g., Intel Core i5).
- Connects to head-node:6379 automatically via Docker Compose. 