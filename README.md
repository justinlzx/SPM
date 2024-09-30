# SPM:

This project contains a frontend and backend application that can be easily spun up using Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Project Structure

```
SPM/
├─ .gitignore
├─ backend/
│  ├─ Dockerfile
│  ├─ main.py
│  ├─ README.md
│  ├─ requirements.txt
│  └─ src/
│     ├─ app.py
│     ├─ arrangements/
│     │  ├─ crud.py
│     │  ├─ exceptions.py
│     │  ├─ models.py
│     │  ├─ routes.py
│     │  ├─ schemas.py
│     │  └─ utils.py
│     ├─ auth/
│     │  ├─ models.py
│     │  ├─ routes.py
│     │  └─ utils.py
│     ├─ base.py
│     ├─ database.py
│     ├─ email/
│     │  ├─ config.py
│     │  ├─ models.py
│     │  ├─ routes.py
│     │  └─ schemas.py
│     ├─ employees/
│     │  ├─ crud.py
│     │  ├─ models.py
│     │  ├─ routes.py
│     │  └─ schemas.py
│     ├─ health/
│     │  └─ health.py
│     ├─ init_db/
│     │  ├─ auth.csv
│     │  ├─ employee.csv
│     │  └─ load_data.py
│     └─ notifications/
│        └─ email_notifications.py
├─ docker-compose.yaml
├─ frontend/
│  ├─ .env
│  ├─ .gitignore
│  ├─ Dockerfile
│  ├─ nginx.conf
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public/
│  │  ├─ favicon.ico
│  │  ├─ index.html
│  │  ├─ logo192.png
│  │  ├─ logo512.png
│  │  ├─ manifest.json
│  │  └─ robots.txt
│  ├─ README.md
│  ├─ src/
│  │  ├─ App.css
│  │  ├─ App.tsx
│  │  ├─ common/
│  │  │  ├─ Footer.tsx
│  │  │  ├─ Header.tsx
│  │  │  ├─ Layout.tsx
│  │  │  └─ SnackBar.tsx
│  │  ├─ components/
│  │  │  ├─ forms/
│  │  │  │  ├─ Recurring.tsx
│  │  │  │  ├─ test.tsx
│  │  │  │  └─ WfhForm.tsx
│  │  │  └─ staffView/
│  │  │     ├─ DashboardCards.tsx
│  │  │     └─ RequestList.tsx
│  │  ├─ context/
│  │  │  ├─ AppContextProvider.tsx
│  │  │  └─ UserContextProvider.tsx
│  │  ├─ hooks/
│  │  │  └─ auth/
│  │  │     ├─ auth.ts
│  │  │     ├─ auth.utils.ts
│  │  │     └─ health/
│  │  │        ├─ health.ts
│  │  │        └─ health.utils.ts
│  │  ├─ index.css
│  │  ├─ index.tsx
│  │  ├─ logo.svg
│  │  ├─ pages/
│  │  │  ├─ home/
│  │  │  │  └─ HomePage.tsx
│  │  │  ├─ login-signup/
│  │  │  │  ├─ LoginPage.tsx
│  │  │  │  └─ SignUpPage.tsx
│  │  │  ├─ pendingrequests/
│  │  │  │  └─ Pendingrequests.tsx
│  │  │  └─ staff/
│  │  │     ├─ RequestPage.tsx
│  │  │     └─ StaffHomePage.tsx
│  │  ├─ react-app-env.d.ts
│  │  ├─ reportWebVitals.ts
│  │  ├─ router/
│  │  │  ├─ Routes.tsx
│  │  │  ├─ test.tsx
│  │  │  └─ TestPage.tsx
│  │  ├─ setupTests.ts
│  │  ├─ theme.js
│  │  └─ utils/
│  │     └─ auth.ts
│  ├─ tailwind.config.js
│  └─ tsconfig.json
├─ README.md
└─ scripts/
   ├─ setup.bat
   └─ setup.sh
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
