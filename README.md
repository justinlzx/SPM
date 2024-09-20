# SPM:

This project contains a frontend and backend application that can be easily spun up using Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Project Structure

```
myapp/
├── frontend/
│   ├── src/
│   │   ├── common/
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── router/
│   │   ├── tests/
│   │   └── utils/
│   ├── Dockerfile
│   └── ...
├── backend/
│   ├── src/
│   │   ├── employees/
│   │   │   ├── crud.py
│   │   │   ├── models.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── <other services...>/
│   │   ├── database.py
│   │   └── app.py
│   ├── Dockerfile
│   └── main.py
├── config/
├── docker-compose.yaml
└── README.md
```

## Getting Started
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

### Start the application

Follow these steps to get your development environment running:

1. Start the application using Docker Compose:

   ```
   docker-compose up -d
   ```

   This command will build the images if they don't exist and start the containers in detached mode.

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

#### Services

The `docker-compose.yaml` file defines the following services:

- `frontend`: React application served by Nginx
- `backend`: FastAPI server

#### Development

To make changes to the application:

(Backend code should automatically update the app in the container, frontend still configuring. Otherwise, follow the steps below)

1. Modify the code in the `frontend/` or `backend/` directories.
2. Rebuild and restart the containers:

   ```
   docker-compose up -d --build
   ```

   ### Starting Individual Components

   Frontend: [HERE](frontend/README.md)
   Backend: [HERE](backend/README.md)

## Stopping the Application

To stop the application and remove the containers:

```
docker-compose down
```

To stop the application and remove the containers, networks, and volumes:

```
docker-compose down -v
```

## Logs

To view the logs of all services:

```
docker-compose logs
```

To view logs for a specific service:

```
docker-compose logs frontend
```

or

```
docker-compose logs backend
```

## Troubleshooting

If you encounter any issues:

1. Ensure all required ports are free and not used by other applications.
2. Check the logs for any error messages.
3. Try rebuilding the images: `docker-compose build --no-cache`
