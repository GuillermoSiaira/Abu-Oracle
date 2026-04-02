# Docker + WSL2 Setup Fix

## Root Cause

Docker Desktop was not using the WSL2 backend for container execution. Additionally, Ubuntu WSL2 distribution was not auto-mounting Windows drives under `/mnt`, preventing Docker from accessing project files.

## Fix Steps

### 1. Enable systemd in WSL2

Edit `/etc/wsl.conf` in your Ubuntu distribution:

```bash
sudo nano /etc/wsl.conf
```

Add the following configuration:

```ini
[boot]
systemd=true
```

### 2. Restart WSL

Shut down all WSL instances from PowerShell:

```powershell
wsl --shutdown
```

Restart your Ubuntu distribution to apply changes.

### 3. Enable WSL Integration in Docker Desktop

Open Docker Desktop → Settings → Resources → WSL Integration:
- Enable "Use the WSL 2 based engine"
- Enable integration with your Ubuntu distribution
- Click "Apply & Restart"

### 4. Verify Docker Context

Check that Docker is using the correct context:

```bash
docker context ls
```

Expected output should show `default` or `desktop-linux` as active with `DOCKER ENDPOINT` pointing to a Unix socket.

### 5. Rebuild Containers

Navigate to your project directory and rebuild:

```bash
cd /mnt/d/projects/AI_Oracle
docker compose up -d --build
```

## Verification Checklist

- [ ] `docker ps` shows running containers
- [ ] Docker Desktop UI lists `ai_oracle`, `abu_engine`, `lilly_engine`, `next_app`
- [ ] Abu Engine responds at http://localhost:8000
- [ ] Next.js app responds at http://localhost:3000
- [ ] Lilly Engine responds at http://localhost:8001

## Troubleshooting

If containers still don't appear:
- Verify `/mnt/d` is accessible in WSL: `ls /mnt/d`
- Check Docker daemon is running: `docker info`
- Review Docker Desktop logs for integration errors
