#!/bin/bash

# Function to check for Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_EXEC="python3"
    elif command -v python &> /dev/null; then
        PYTHON_EXEC="python"
    else
        echo "Python is not installed. Please install Python and try again."
        exit 1
    fi
}

# Check for Python (either python3 or python)
check_python

# Check if the venv directory exists, if not, create a virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating a new virtual environment..."
    $PYTHON_EXEC -m venv venv
else
    echo "Virtual environment found."
fi

# Activate the virtual environment using the . (dot) command instead of source
echo "Activating virtual environment..."
. venv/bin/activate  # Using . (dot) for broader shell support

# Upgrade pip to the latest version
echo "Upgrading pip..."
pip install --upgrade pip

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found!"
    exit 1
fi

# Install the required Python packages
echo "Installing Python packages from requirements.txt..."
pip install -r requirements.txt

echo "All packages installed successfully."
