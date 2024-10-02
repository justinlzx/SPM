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

## API Endpoints
### Authentication (auth)
* **POST** `/auth/register`
  Registers a new user by accepting email, username, password, and role. Returns the UUID for the user.
* **POST** `/auth/login`
    Logs in a user by validating their username and password.

### Users
* **GET** `/users/email/{email}`
Fetch a user by their email address.
* **GET**  `/users/username/{username}`
Fetch a user by their username.

## Example Requests
### Register a User
```bash
curl -X POST "http://127.0.0.1:8000/auth/register" -H "Content-Type: application/x-www-form-urlencoded" -d "email=user@example.com&username=user123&password=pass123&role=user"
```
### Login a User
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=user123&password=pass123"
```
### Fetch a User by Email
```bash
curl -X GET "http://127.0.0.1:8000/users/email/user@example.com" -H "accept: application/json"
```
### Fetch a User by Username
```bash
curl -X GET "http://127.0.0.1:8000/users/username/user123" -H "accept: application/json"
```
