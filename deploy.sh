#!/bin/bash

# Monitor Hub Deployment Script
# Run this on your Ubuntu server to deploy the monitoring system

set -e

echo "🚀 Deploying Monitor Hub..."

# ===== CONFIG =====
INSTALL_DIR="/opt/monitor-hub"
SERVICE_USER="monitor"
VENV_DIR="$INSTALL_DIR/venv"

# ===== 1. CREATE SERVICE USER =====
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "📝 Creating service user: $SERVICE_USER"
    sudo useradd -r -s /bin/false $SERVICE_USER
fi

# ===== 2. SETUP DIRECTORY =====
echo "📁 Setting up directory: $INSTALL_DIR"
sudo mkdir -p $INSTALL_DIR
sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# ===== 3. COPY FILES =====
echo "📦 Copying files..."
cp -r ./* $INSTALL_DIR/
sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# ===== 4. CREATE VIRTUAL ENV =====
echo "🐍 Creating virtual environment..."
cd $INSTALL_DIR
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# ===== 5. INSTALL DEPENDENCIES =====
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# ===== 6. SETUP ENV FILE =====
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example $INSTALL_DIR/.env
    echo "⚠️  EDIT $INSTALL_DIR/.env WITH YOUR CONFIG!"
fi

# ===== 7. INSTALL PM2 =====
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2..."
    sudo npm install -g pm2
fi

# ===== 8. UPDATE ECOSYSTEM CONFIG =====
echo "⚙️  Updating ecosystem.config.json with actual paths..."
sed -i "s|/path/to/monitoring-system|$INSTALL_DIR|g" ecosystem.config.json

# ===== 9. START SERVICE =====
echo "🚀 Starting Monitor Hub..."
pm2 start ecosystem.config.json
pm2 save
pm2 startup

echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit $INSTALL_DIR/.env with your Slack tokens"
echo "2. Restart: pm2 restart monitor-hub"
echo "3. Check logs: pm2 logs monitor-hub"
echo "4. Check status: pm2 status"
