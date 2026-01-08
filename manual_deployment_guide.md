# Manual Server Deployment Guide (Shell)

This guide walks you through deploying the `ApiComparator` application directly on a Linux server (Ubuntu/CentOS) using standard shell commands, without Docker.

## Prerequisites

1.  **Python 3.9+**: Ensure Python is installed.
    *   Check: `python3 --version`
2.  **Git**: To download your code (optional if you use SCP/SFTP).
3.  **Pip**: Python package manager.

## Installation Steps

### 1. Upload/Clone Code
Move your project files to the server, for example to `/opt/ApiComparator` or `~/ApiComparator`.

```bash
cd ~/ApiComparator
```

### 2. Install Dependencies
Install the required libraries (ensure you have necessary permissions, e.g., sudo if installing globally):

```bash
pip install -r requirements.txt
```

### 4. Setup Startup Script
I've included a helper script `run.sh`. Make it executable:

```bash
chmod +x run.sh
```

## Running the Application

### Option 1: Temporary (Interactive)
Good for testing if it works.
```bash
./run.sh
```
*   Press `Ctrl+C` to stop.

### Option 2: Background (Persistent)
To keep the app running after you disconnect from the server, use `nohup`.

**Start:**
```bash
nohup ./run.sh > app.log 2>&1 &
```
*   `nohup`: Prevents the process from being killed when you logout.
*   `> app.log 2>&1`: Redirects output and errors to `app.log` file.
*   `&`: Runs it in the background.

**Check Status:**
```bash
ps aux | grep streamlit
```

**Stop:**
1.  Find the process ID (PID) using `ps aux | grep streamlit`.
2.  Kill it: `kill <PID>`

## Accessing the App
Open your browser and visit:
`http://<YOUR_SERVER_IP>:8501`

*(Ensure your server's firewall allows traffic on port 8501)*
