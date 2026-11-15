#!/usr/bin/env bash
# ==============================================================================
# AI Fitness Coach Appliance Installer for Raspberry Pi 4B (Bookworm 64-bit)
# ==============================================================================
set -euo pipefail

echo "=================================================================="
echo "    Installing Industry-Grade AI Fitness Coach Kiosk Appliance    "
echo "=================================================================="

# Ensure running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo. Try: sudo ./install.sh"
   exit 1
fi

APP_DIR="/opt/yoga-app"
SERVICE_USER="pi"

echo "1. Installing base system packages..."
apt-get update -y
apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-picamera2 \
    python3-libcamera \
    chromium-browser \
    unclutter \
    espeak-ng \
    libatlas-base-dev \
    sqlite3 \
    curl \
    git

echo "2. Deploying application to ${APP_DIR}..."
mkdir -p "${APP_DIR}"
cp -r . "${APP_DIR}/"
chown -R ${SERVICE_USER}:${SERVICE_USER} "${APP_DIR}"

echo "3. Creating Python 3.11+ Virtual Environment (with system-site-packages for Picamera2)..."
sudo -u ${SERVICE_USER} python3 -m venv --system-site-packages "${APP_DIR}/backend/venv"

echo "4. Installing Python dependencies..."
sudo -u ${SERVICE_USER} "${APP_DIR}/backend/venv/bin/pip" install --upgrade pip
sudo -u ${SERVICE_USER} "${APP_DIR}/backend/venv/bin/pip" install \
    Flask==3.0.3 \
    Flask-SocketIO==5.3.6 \
    Flask-SQLAlchemy==3.1.1 \
    Flask-Cors==4.0.1 \
    PyJWT==2.9.0 \
    python-socketio==5.11.3 \
    python-engineio==4.9.1 \
    Werkzeug==3.0.4 \
    numpy>=1.24.0 \
    scipy>=1.10.0 \
    pyyaml>=6.0 \
    pydantic>=2.0 \
    argon2-cffi>=23.0 \
    pytest>=8.0 \
    reportlab>=4.0 \
    psutil>=5.9.0

echo "5. Installing Systemd Services..."
cp "${APP_DIR}/deploy/systemd/ai-coach-backend.service" /etc/systemd/system/
cp "${APP_DIR}/deploy/systemd/ai-coach-kiosk.service" /etc/systemd/system/
systemctl daemon-reload

echo "6. Enabling Auto-Start at Boot..."
systemctl enable ai-coach-backend.service
systemctl enable ai-coach-kiosk.service

echo "=================================================================="
echo " Installation Complete! To start immediately, run:"
echo "   sudo systemctl start ai-coach-backend"
echo "   sudo systemctl start ai-coach-kiosk"
echo "=================================================================="
