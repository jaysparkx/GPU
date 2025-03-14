# Mac Provider Client Setup

## Prerequisites
- Docker installed (Docker Desktop on macOS)
- macOS system (will not run on Windows)

## Steps to Join as a Worker
1. **Pull Docker Image**:
   ```bash
   docker pull yourdockerhubusername/provider_client_mac:latest
   ```
   (Replace `yourdockerhubusername` with the actual Docker Hub username after publishing.)

2. **Run Docker Container**:
   ```bash
   docker run -d --name provider_client_mac yourdockerhubusername/provider_client_mac:latest
   ```

## Notes
- Designed for Mac M1/M2 (MPS GPU) or CPU.
- Connects to head-node:6379 automatically via Docker Compose. 