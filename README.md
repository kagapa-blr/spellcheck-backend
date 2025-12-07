# Spellcheck Project

## Overview

The Spellcheck Project is a Python-based application designed to provide efficient spell-checking capabilities. It utilizes advanced algorithms, including Bloom filters and SymSpell, to quickly identify and correct misspelled words in various text documents. This project is built using **FastAPI** and deployed with **Gunicorn**.

* **Frontend:** React JS
* **Backend:** FastAPI
* **Application server:** Uvicorn / Gunicorn

## Table of Contents

* [Features](#features)
* [Installation](#installation)
* [Configuration](#configuration)
* [Local Setup (FastAPI Development)](#local-setup-fastapi-development)
* [Frontend Setup](#frontend-setup)
* [Logging](#logging)
* [Contributing](#contributing)
* [License](#license)

## Features

* Fast spell-checking using **Bloom filters** and **SymSpell**.
* Supports processing of various text formats.
* Easy integration with other applications.
* User-friendly API for spell-checking functionalities.
* Admin and user authentication with **JWT**.
* Multilingual support (English & Kannada).

## Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/kagapa-blr/spellcheck-backend.git
cd spellcheck-backend
```

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

1. Update the `.env` file with correct credentials:

```
APP_ENV=development
DATABASE_URL=your-database-url
JWT_SECRET_KEY=your-secret-key
```

2. Check configuration path of the service file.

3. Configure the systemd service (for production):

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

## Local Setup (FastAPI Development)

You can run the backend locally without systemd or Gunicorn.

### 1. Install dependencies

Make sure your virtual environment is activated:

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

Ensure `.env` exists in the project root:

```
APP_ENV=development
DATABASE_URL=your-local-db-url
JWT_SECRET_KEY=your-secret-key
```

### 3. Run FastAPI locally

```bash
uvicorn app.main:app --reload
```

* `--reload` automatically restarts the server on file changes.
* Default local URL: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### 4. API Documentation

Swagger UI:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

## Frontend Setup (React.js)

### 1. Navigate to frontend folder

```bash
cd frontend
npm install
```

### 2. Run development server

```bash
npm run dev
```

* Default URL: **[http://localhost:5173](http://localhost:5173)** (Vite)
* The frontend communicates with the FastAPI backend using JWT authentication.

### 3. Build for production

```bash
npm run build
```

## Logging

* Backend logs are stored according to your systemd service configuration.
* You can also view logs in real-time:

```bash
journalctl -u spellcheck.service -f
```

* Frontend errors are visible in browser developer tools (Console tab).

## Contributing

* Fork the repository and create a feature branch.
* Submit pull requests with detailed descriptions.
* Ensure all code passes linting and tests.

## License

This project is licensed under the **MIT License**.

## Author

**Ravikumar Pawar**

* GitHub: [https://github.com/kagapa-blr](https://github.com/kagapa-blr)
