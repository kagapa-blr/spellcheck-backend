# Spellcheck Project

## Overview

The Spellcheck Project is a Python-based application designed to provide efficient spell-checking capabilities.  
It utilizes advanced algorithms, including Bloom filters and SymSpell, to quickly identify and correct misspelled words in various text documents.  
This project is built using FastAPI and deployed with Gunicorn.

**Frontend:** React JS  
**Backend:** FastAPI  
**Application server:** Uvicorn / Gunicorn  

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Local Setup (FastAPI Development)](#local-setup-fastapi-development)
- [Database Migration](#database-migration)
- [Frontend Setup](#frontend-setup-reactjs)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Features

- Fast spell-checking using Bloom filters and SymSpell.  
- Supports processing of various text formats.  
- Easy integration with other applications.  
- User-friendly API for spell-checking functionalities.  
- Admin and user authentication with JWT.  
- Multilingual support (English and Kannada).  

---

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

---

## Configuration

Update the `.env` file with correct credentials:

```env
APP_ENV=development
DATABASE_URL=your-database-url
JWT_SECRET_KEY=your-secret-key
```

Configure the systemd service (for production):

```bash
sudo systemctl enable spellcheck.service
sudo systemctl start spellcheck.service
sudo systemctl stop spellcheck.service
sudo systemctl restart spellcheck.service
sudo systemctl status spellcheck.service
```

---

## Local Setup (FastAPI Development)

Run the backend locally:

```bash
uvicorn app.main:app --reload
```

Local URL: http://127.0.0.1:8000  
Swagger: http://127.0.0.1:8000/docs  
ReDoc: http://127.0.0.1:8000/redoc  

---

## Database Migration

```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "initial migration"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
alembic downgrade <revision_id>
alembic stamp head
alembic revision -m "add index to words table"
```

---

## Frontend Setup (React.js)

```bash
cd frontend
npm install
npm run dev
npm run build
```

---

## Logging

```bash
journalctl -u spellcheck.service -f
```

---

## Contributing

- Fork the repository and create a feature branch.  
- Submit pull requests with detailed descriptions.  
- Ensure all code passes linting and tests.  

---

## License

This project is licensed under the MIT License.

---

## Author

Ravikumar Pawar  
GitHub: https://github.com/kagapa-blr
