# SPM Project - Mee Rebus

## Setup
### Requirements
* Python 3.8 or higher
* SQLite (built-in with Python)

### Setup development environment
1. Ensure you are in the project root directory
2. (MacOS/Linux users only) Give permissions to run the setup script
```bash
chmod +x ./scripts/setup.sh
```
3. Run the setup script

MacOS/Linux users:
```bash
./scripts/setup.sh
```

Windows users:
```bash
scripts\setup.bat
```

4. Activate the `project_venv` **before starting any development work**

MacOS/Linux users:
```bash
source project_venv/bin/activate
```

Windows users:
```bash
.\project_venv\Scripts\activate
```

## Running the backend application (without Docker)
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
