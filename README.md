**# Spellcheck Project

## Overview

The Spellcheck Project is a Python-based application designed to provide efficient spell-checking capabilities. It
utilizes advanced algorithms, including Bloom filters and SymSpell, to quickly identify and correct misspelled words in
various text documents. This project is built using Fast API and deployed with Gunicorn.

- frontend: React JS
- backend: Fast API
- Application server: Uvicorn server

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

## Features

- Fast spell-checking using Bloom filters and SymSpell.
- Supports processing of various text formats.
- Easy integration with other applications.
- User-friendly API for spell-checking functionalities.

## Installation

To get started, clone the repository and install the required dependencies.

```bash
git clone https://github.com/kagapa-blr/spellcheck-backend.git
cd spellcheck-backend
```

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

1. update the .env with correct credentials
2. check configuration path of service file
3. configure service with below commands
    ```bash 
    # Enable the service to start on boot
    sudo systemctl enable spellcheck.service
    
    # Start the service immediately
    sudo systemctl start spellcheck.service
    
    # Stop the service if it's currently running
    sudo systemctl stop spellcheck.service
    
    # Restart the service to apply any changes
    sudo systemctl restart spellcheck.service
    
    # Check the status of the service to see if it's running correctly
    sudo systemctl status spellcheck.service
       ```