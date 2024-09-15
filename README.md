# SPM Project - Mee Rebus

## Setup
### Requirements
* Python 3.8 or higher
* SQLite (built-in with Python)

### Install Pre-Commit Hook
Pre-commit hooks run code quality checks everytime you commit. Hooks to be used are specified in .pre-commit-config.yaml.

*NOTE: pre-commit will only work using the ```git commit``` command in terminal. It will not work using the VSCode Source Control GUI.

1. (Optional) Create and activate a Python venv

For macOS:
```bash
python -m venv <name_of_venv>
source <name_of_venv>/bin/activate
```
For Windows:
```bash
python -m venv <name_of_venv>
<name_of_venv>/bin/activate
```

2. Install the pre-commit hook manager
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

## Running the backend application
1. Change to the backend directory
```bash
cd backend
```

2. Run the app
```bash
python -m main
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
