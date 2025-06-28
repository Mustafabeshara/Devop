#!/bin/bash

# 🚀 Kimi-Dev-72B Development Environment Startup Script
# This script sets up and starts the complete development environment

echo "🌐 Starting Kimi-Dev-72B Development Environment..."
echo "================================================="

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "kimi-dev-workspace.code-workspace" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Check and set up backend environment
print_status "Setting up backend environment..."
cd cloud-browser-backend

if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

print_status "Activating virtual environment..."
source venv/bin/activate

print_status "Installing/updating backend dependencies..."
pip install -r requirements.txt

# Step 2: Initialize database if needed
if [ ! -f "database/app.db" ]; then
    print_status "Initializing database..."
    python src/main.py --init-db
fi

# Step 3: Set up frontend environment
print_status "Setting up frontend environment..."
cd ../cloud-browser-frontend

if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Step 4: Create .env files if they don't exist
cd ..
if [ ! -f "cloud-browser-backend/.env" ]; then
    print_status "Creating backend environment file..."
    cat > cloud-browser-backend/.env << EOF
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
DATABASE_URL=sqlite:///database/app.db
DOCKER_HOST=unix:///var/run/docker.sock
LOG_LEVEL=DEBUG
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
fi

if [ ! -f "cloud-browser-frontend/.env" ]; then
    print_status "Creating frontend environment file..."
    cat > cloud-browser-frontend/.env << EOF
VITE_API_BASE_URL=http://localhost:5001
VITE_APP_NAME=Kimi-Dev-72B Cloud Browser
VITE_APP_VERSION=1.0.0
EOF
fi

# Step 5: Display startup information
echo ""
print_success "Development environment setup complete!"
echo ""
echo "🔗 Quick Access Links:"
echo "  • Live Website: https://nybbgll9qi.space.minimax.io"
echo "  • Admin Login: admin@secure-kimi.local / SecureKimi2024!"
echo ""
echo "💻 Development Servers:"
echo "  • Backend API: http://localhost:5001"
echo "  • Frontend Dev: http://localhost:3000 (if running locally)"
echo ""
echo "🛠️ Available Commands:"
echo "  • Start Backend: cd cloud-browser-backend && source venv/bin/activate && python src/main.py"
echo "  • Start Frontend: cd cloud-browser-frontend && npm run dev"
echo "  • Docker Deploy: docker-compose up --build"
echo "  • Open VSCode: code kimi-dev-workspace.code-workspace"
echo ""

# Step 6: Ask user what they want to do
echo "What would you like to do?"
echo "1) Start backend server only"
echo "2) Start frontend development server only"
echo "3) Start both servers"
echo "4) Open in VSCode"
echo "5) Open live website"
echo "6) Exit"

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        print_status "Starting backend server..."
        cd cloud-browser-backend
        source venv/bin/activate
        python src/main.py
        ;;
    2)
        print_status "Starting frontend development server..."
        cd cloud-browser-frontend
        npm run dev
        ;;
    3)
        print_status "Starting both servers..."
        # Start backend in background
        cd cloud-browser-backend
        source venv/bin/activate
        python src/main.py &
        BACKEND_PID=$!
        
        # Start frontend
        cd ../cloud-browser-frontend
        npm run dev &
        FRONTEND_PID=$!
        
        # Wait for user to stop
        echo "Press Ctrl+C to stop both servers"
        trap "kill $BACKEND_PID $FRONTEND_PID" INT
        wait
        ;;
    4)
        print_status "Opening project in VSCode..."
        code kimi-dev-workspace.code-workspace
        ;;
    5)
        print_status "Opening live website..."
        python3 -c "import webbrowser; webbrowser.open('https://nybbgll9qi.space.minimax.io')"
        ;;
    6)
        print_success "Setup complete. Happy coding! 🚀"
        ;;
    *)
        print_warning "Invalid choice. Setup complete."
        ;;
esac
