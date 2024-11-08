# SPM Project - Mee Rebus

## Setup
### Requirements
* Python 3.8 or higher
* SQLite (built-in with Python)

### Install Pre-Commit Hook
Pre-commit hooks run code quality checks everytime you commit. Hooks to be used are specified in .pre-commit-config.yaml, and more hooks can be added from https://github.com/pre-commit/pre-commit-hooks

1. Create and activate a Python venv
For macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```
For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install the pre-commit package manager
```bash
pip install pre-commit
```

3. Install the pre-commit hooks
```bash
pre-commit install
```

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

## Running the Application
If you're **not** already in the backend directory:
```bash
cd backend
python -B -m uvicorn src.app:app --reload
```

If you're already in the backend directory:
```bash
python -B -m uvicorn src.app:app --reload
```

## Accessing API Documentation
After running the application, you can access the interactive API documentation provided by Swagger at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
