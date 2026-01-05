#!/bin/bash
set -e

# Juli Backend - DigitalOcean Server Setup Script
# Run this once on a fresh Ubuntu 24.04 droplet

echo "=== Juli Backend Server Setup ==="
echo "Started at: $(date)"

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "Installing dependencies..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed"
fi

# Configure firewall
echo "Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 8000/tcp  # API
ufw --force enable

# Create app directory
echo "Creating application directory..."
mkdir -p /opt/juli_backend
cd /opt/juli_backend

# Clone repository (you'll need to set up SSH keys or use HTTPS)
echo ""
echo "=== Manual Steps Required ==="
echo ""
echo "1. Clone your repository:"
echo "   cd /opt/juli_backend"
echo "   git clone https://github.com/YOUR_USERNAME/juli_backend.git ."
echo ""
echo "2. Create environment file:"
echo "   cp .env.production.example .env"
echo "   nano .env  # Edit with your production values"
echo ""
echo "3. Generate a secure SECRET_KEY:"
echo "   openssl rand -hex 32"
echo ""
echo "4. Run initial deployment:"
echo "   chmod +x scripts/deploy.sh"
echo "   ./scripts/deploy.sh"
echo ""
echo "5. Configure GitHub Secrets for CI/CD:"
echo "   - DROPLET_HOST: $(curl -s ifconfig.me)"
echo "   - DROPLET_USER: root"
echo "   - DROPLET_SSH_KEY: (your private SSH key)"
echo ""
echo "=== Server Setup Complete ==="
echo "Finished at: $(date)"
