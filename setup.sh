#!/bin/bash

echo "======================================"
echo "Agentic Google Workspace AI Setup"
echo "======================================"
echo ""

# Create necessary directories
echo "Creating directory structure..."
mkdir -p backend/app/{models,services,integrations,api/routes,utils,mcp_servers}
mkdir -p backend/credentials
mkdir -p backend/logs
mkdir -p backend/tests
mkdir -p frontend/src/{components/{Chat,Gmail,Docs,Calendar,Sheets,Forms,Common},views,stores,services,router,styles,utils}
mkdir -p frontend/public
mkdir -p mcp_config
mkdir -p docker

echo "✓ Directories created"
echo ""

# Backend setup
echo "Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created - PLEASE EDIT THIS FILE WITH YOUR CREDENTIALS"
else
    echo "⚠ .env file already exists, skipping..."
fi

cd ..

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend

# Install npm dependencies
if [ -f "package.json" ]; then
    echo "Installing Node dependencies..."
    npm install
    echo "✓ Dependencies installed"
else
    echo "⚠ package.json not found, skipping npm install"
fi

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cp .env.example .env 2>/dev/null || echo "⚠ .env.example not found"
fi

cd ..


