# Streamlit App Deployment Guide

This guide explains how to deploy your `ApiComparator` application to a server using Docker. This ensures the application runs consistently regardless of the server environment.

## Prerequisites

1.  **Docker**: Ensure Docker is installed on your server.
    *   Ubuntu: `sudo apt-get install docker.io`
    *   CentOS: `sudo yum install docker`
    *   Verification: Run `docker --version`.

2.  **File Transfer**: You need to upload your project files to the server (e.g., using `scp`, `rsync`, or Git).

## Deployment Steps

### 1. Prepare Your Environment
Navigate to your project directory on the server:
```bash
cd /path/to/ApiComparator
```
Ensure the following files are present:
*   `Dockerfile` in the root (created/updated for you).
*   `requirements.txt` (dependencies list).
*   `app.py` and other source files.

### 2. Build the Docker Image
Run the following command to build the image. This may take a few minutes the first time.
```bash
docker build -t api-comparator .
```
*   `-t api-comparator`: Tags the image with the name "api-comparator".
*   `.`: Specifies the current directory as the build context.

### 3. Run the Container
Start the application container:
```bash
docker run -d -p 8501:8501 --name api-comparator-app --restart always api-comparator
```
*   `-d`: Runs in detached mode (background).
*   `-p 8501:8501`: Maps port 8501 of the server to port 8501 of the container.
*   `--name api-comparator-app`: Assigns a name to the running container.
*   `--restart always`: Automatically restarts the app if it crashes or the server reboots.

### 4. Verify/Access
Open your browser and visit:
`http://<YOUR_SERVER_IP>:8501`

To check logs if something goes wrong:
```bash
docker logs api-comparator-app
```

## Maintenance

*   **Stop**: `docker stop api-comparator-app`
*   **Start**: `docker start api-comparator-app`
*   **Update**:
    1.  `git pull` (or re-upload files)
    2.  `docker build -t api-comparator .`
    3.  `docker stop api-comparator-app`
    4.  `docker rm api-comparator-app`
    5.  Run the `docker run` command from step 3 again.

## Data Persistence & Updates

> [!IMPORTANT]
> The `data/` directory contains your production database (projects, environments, APIs).

**When deploying updates:**
1.  **Do NOT** copy the local `data/` folder to the server if you want to keep potential server-side changes or user data.
2.  If using `rsync` or `scp`, exclude the data directory:
    ```bash
    rsync -av --exclude 'data' ./ user@server:~/app/
    ```
3.  If using Docker, ensure you mount a volume for `data/` so it persists across container restarts:
    ```bash
    docker run -d -p 8501:8501 -v $(pwd)/data:/app/data --name api-comparator api-comparator
    ```
