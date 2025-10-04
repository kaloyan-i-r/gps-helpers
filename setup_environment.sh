#!/bin/bash

# GPS Helpers Environment Setup Script
# This script sets up a Python virtual environment and installs all dependencies
# for the GPS helpers tools (GPS Route Manager and GPX Fixer)

set -e  # Exit on any error

# Colors for output
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

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

print_status "GPS Helpers Environment Setup"
print_status "================================"
print_status "Script directory: $SCRIPT_DIR"

# Check if Python 3 is available
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        if [[ $PYTHON_VERSION == Python\ 3.* ]]; then
            print_success "Python 3 found: $PYTHON_VERSION"
            PYTHON_CMD="python"
        else
            print_error "Python 3 is required, but only Python 2 was found"
            exit 1
        fi
    else
        print_error "Python 3 is not installed or not in PATH"
        print_status "Please install Python 3.6 or higher and try again"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists at $VENV_DIR"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        else
            print_status "Using existing virtual environment"
            return 0
        fi
    fi
    
    print_status "Creating new virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Virtual environment created successfully"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    
    # Source the activation script
    source "$VENV_DIR/bin/activate"
    
    if [ $? -eq 0 ]; then
        print_success "Virtual environment activated"
        
        # Update pip
        print_status "Updating pip..."
        pip install --upgrade pip
        
        print_status "Python path: $(which python)"
        print_status "Pip path: $(which pip)"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Create requirements.txt if it doesn't exist
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_status "Creating requirements.txt..."
        cat > "$REQUIREMENTS_FILE" << EOF
# GPS Helpers Dependencies
gpxpy>=1.5.0

# Optional dependencies for enhanced functionality
# matplotlib>=3.5.0  # For route visualization (uncomment if needed)
# folium>=0.12.0     # For interactive maps (uncomment if needed)
EOF
        print_success "Created requirements.txt"
    fi
    
    # Install from requirements.txt
    print_status "Installing packages from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE"
    
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
    
    # Show installed packages
    print_status "Installed packages:"
    pip list | grep -E "(gpxpy|Package)"
}

# Create run scripts
create_run_scripts() {
    print_status "Creating convenience run scripts..."
    
    # Script to run GPS Route Manager
    cat > "$SCRIPT_DIR/run_gui.sh" << 'EOF'
#!/bin/bash
# GPS Route Manager Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

echo "Starting GPS Route Manager..."
source "$VENV_DIR/bin/activate"
python "$SCRIPT_DIR/gps_route_manager.py"
EOF
    
    # Script to run GPX Fixer
    cat > "$SCRIPT_DIR/run_fixer.sh" << 'EOF'
#!/bin/bash
# GPX Fixer Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

echo "Starting GPX Fixer..."
source "$VENV_DIR/bin/activate"
python "$SCRIPT_DIR/gpx_fix.py" "$@"
EOF
    
    # Script to activate environment for manual use
    cat > "$SCRIPT_DIR/activate_env.sh" << 'EOF'
#!/bin/bash
# Activate GPS Helpers Environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

echo "Activating GPS Helpers environment..."
source "$VENV_DIR/bin/activate"
echo "Environment activated! You can now run:"
echo "  python gps_route_manager.py  # Start GUI"
echo "  python gpx_fix.py [options]  # Run GPX fixer"
echo "  deactivate                   # Exit environment"
EOF
    
    # Make scripts executable
    chmod +x "$SCRIPT_DIR/run_gui.sh"
    chmod +x "$SCRIPT_DIR/run_fixer.sh"
    chmod +x "$SCRIPT_DIR/activate_env.sh"
    
    print_success "Created convenience scripts:"
    print_status "  - run_gui.sh      # Launch GPS Route Manager"
    print_status "  - run_fixer.sh    # Launch GPX Fixer with arguments"
    print_status "  - activate_env.sh # Activate environment for manual use"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "$SCRIPT_DIR/routes/original"
    mkdir -p "$SCRIPT_DIR/routes/lockito"
    
    print_success "Created directories:"
    print_status "  - routes/original/ # Place your GPX files here"
    print_status "  - routes/lockito/  # Processed files (auto-created)"
}

# Main setup function
main() {
    print_status "Starting GPS Helpers environment setup..."
    
    check_python
    create_venv
    activate_venv
    install_dependencies
    create_directories
    create_run_scripts
    
    print_success "Setup completed successfully!"
    echo
    print_status "You can now use the GPS helpers in several ways:"
    echo
    print_status "1. Quick start with convenience scripts:"
    print_status "   ./run_gui.sh                    # Start GUI application"
    print_status "   ./run_fixer.sh --profile car    # Run GPX fixer"
    echo
    print_status "2. Manual activation:"
    print_status "   source activate_env.sh          # Activate environment"
    print_status "   python gps_route_manager.py     # Start GUI"
    print_status "   python gpx_fix.py [options]     # Run fixer"
    print_status "   deactivate                      # Exit environment"
    echo
    print_status "3. Direct activation:"
    print_status "   source venv/bin/activate        # Activate manually"
    print_status "   python gps_route_manager.py     # Start GUI"
    print_status "   python gpx_fix.py [options]     # Run fixer"
    echo
    print_status "Next steps:"
    print_status "1. Place your GPX files in the 'routes/original/' directory"
    print_status "2. Run './run_gui.sh' to start the GUI application"
    print_status "3. Or run './run_fixer.sh --profile car' for command-line processing"
    echo
    print_success "Happy GPS route processing!"
}

# Run main function
main "$@"
