# SPM:

This project contains a frontend and backend application that can be easily spun up using Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Project Structure

```
SPM/
├─ .dockerignore
├─ .gitignore
├─ .pre-commit-config.yaml
├─ .pytest_cache/
├─ backend/
│  ├─ .coveragerc
│  ├─ .pytest_cache/
│  ├─ Dockerfile
│  ├─ htmlcov/
│  ├─ main.py
│  ├─ pytest.ini
│  ├─ README.md
│  ├─ requirements.prod.txt
│  ├─ requirements.txt
│  └─ src/
│     ├─ app.py
│     ├─ arrangements/
│     │  ├─ archive/
│     │  │  └─ scheduler.py
│     │  ├─ commons/
│     │  │  ├─ dataclasses.py
│     │  │  ├─ enums.py
│     │  │  ├─ exceptions.py
│     │  │  ├─ models.py
│     │  │  └─ schemas.py
│     │  ├─ crud.py
│     │  ├─ routes.py
│     │  ├─ services.py
│     │  ├─ utils.py
│     │  └─ __init__.py
│     ├─ auth/
│     │  ├─ models.py
│     │  ├─ routes.py
│     │  ├─ utils.py
│     │  └─ __init__.py
│     ├─ base.py
│     ├─ database.py
│     ├─ email/
│     │  ├─ config.py
│     │  ├─ exceptions.py
│     │  ├─ models.py
│     │  ├─ routes.py
│     │  ├─ schemas.py
│     │  └─ __init__.py
│     ├─ employees/
│     │  ├─ crud.py
│     │  ├─ dataclasses.py
│     │  ├─ exceptions.py
│     │  ├─ models.py
│     │  ├─ routes.py
│     │  ├─ schemas.py
│     │  ├─ services.py
│     │  └─ __init__.py
│     ├─ health/
│     │  ├─ health.py
│     │  └─ __init__.py
│     ├─ init_db/
│     │  ├─ auth.csv
│     │  ├─ data_preprocessing.ipynb
│     │  ├─ employee.csv
│     │  ├─ latest_arrangement.csv
│     │  ├─ load_data.py
│     │  └─ __init__.py
│     ├─ logger.py
│     ├─ notifications/
│     │  ├─ commons/
│     │  │  ├─ dataclasses.py
│     │  │  └─ structs.py
│     │  ├─ email_notifications.py
│     │  └─ exceptions.py
│     ├─ schemas.py
│     ├─ tests/
│     │  ├─ arrangements/
│     │  │  ├─ cat.png
│     │  │  ├─ dog.jpg
│     │  │  ├─ dummy.pdf
│     │  │  ├─ test_crud.py
│     │  │  ├─ test_exceptions.py
│     │  │  ├─ test_models.py
│     │  │  ├─ test_routes.py
│     │  │  ├─ test_schemas.py
│     │  │  ├─ test_services.py
│     │  │  ├─ test_utils.py
│     │  │  └─ __init__.py
│     │  ├─ auth/
│     │  │  ├─ test_models.py
│     │  │  ├─ test_routes.py
│     │  │  ├─ test_utils.py
│     │  │  └─ __init__.py
│     │  ├─ email/
│     │  │  ├─ test_exceptions.py
│     │  │  ├─ test_models.py
│     │  │  ├─ test_routes.py
│     │  │  └─ test_schemas.py
│     │  ├─ employees/
│     │  │  ├─ test_crud.py
│     │  │  ├─ test_exceptions.py
│     │  │  ├─ test_models.py
│     │  │  ├─ test_routes.py
│     │  │  ├─ test_services.py
│     │  │  └─ __init__.py
│     │  ├─ init_db/
│     │  │  ├─ test_auth.csv
│     │  │  ├─ test_employee.csv
│     │  │  ├─ test_latest_arrangement.csv
│     │  │  ├─ test_load_data.py
│     │  │  └─ __init__.py
│     │  ├─ notifications/
│     │  │  └─ test_email_notifications.py
│     │  ├─ test_utils.py
│     │  └─ __init__.py
│     ├─ utils.py
│     └─ __init__.py
├─ cypress/
│  ├─ downloads/
│  ├─ e2e/
│  │  ├─ acceptrequest.cy.js
│  │  ├─ cancelrequest.cy.js
│  │  ├─ createrequest.cy.js
│  │  ├─ delegation.cy.js
│  │  ├─ departmentoverview.cy.js
│  │  ├─ login.cy.js
│  │  ├─ teamview.cy.js
│  │  └─ withdrawrequest.cy.js
│  ├─ fixtures/
│  │  └─ example.json
│  └─ support/
│     ├─ commands.js
│     └─ e2e.js
├─ cypress.config.js
├─ docker-compose.yaml
├─ frontend/
│  ├─ .gitignore
│  ├─ .pytest_cache/
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
│  │  │  ├─ DashboardCards.tsx
│  │  │  ├─ DragAndDrop.tsx
│  │  │  ├─ Filters.tsx
│  │  │  ├─ Footer.tsx
│  │  │  ├─ Header.tsx
│  │  │  ├─ Layout.tsx
│  │  │  ├─ LoadingSpinner.tsx
│  │  │  ├─ Search.tsx
│  │  │  ├─ Sidebar.tsx
│  │  │  └─ SnackBar.tsx
│  │  ├─ components/
│  │  │  ├─ requests/
│  │  │  │  ├─ DateRow.tsx
│  │  │  │  ├─ DocumentDialog.tsx
│  │  │  │  ├─ EmployeeRow.tsx
│  │  │  │  └─ Recurring.tsx
│  │  │  └─ WFHRequestTable.tsx
│  │  ├─ context/
│  │  │  ├─ AppContextProvider.tsx
│  │  │  ├─ FilterContextProvider.tsx
│  │  │  └─ UserContextProvider.tsx
│  │  ├─ hooks/
│  │  │  ├─ arrangement/
│  │  │  │  ├─ arrangement.ts
│  │  │  │  └─ arrangement.utils.ts
│  │  │  ├─ auth/
│  │  │  │  ├─ auth.ts
│  │  │  │  └─ auth.utils.ts
│  │  │  ├─ employee/
│  │  │  │  ├─ delegation.utils.ts
│  │  │  │  └─ employee.utils.ts
│  │  │  └─ health/
│  │  │     ├─ health.ts
│  │  │     └─ health.utils.ts
│  │  ├─ index.css
│  │  ├─ index.tsx
│  │  ├─ logo.svg
│  │  ├─ pages/
│  │  │  ├─ hr/
│  │  │  │  ├─ chart/
│  │  │  │  │  └─ Chart.tsx
│  │  │  │  ├─ DepartmentOverviewPage.tsx
│  │  │  │  ├─ RequestHistory.tsx
│  │  │  │  ├─ Statistics.tsx
│  │  │  │  └─ StatsFilters.tsx
│  │  │  ├─ login-signup/
│  │  │  │  ├─ LoginPage.tsx
│  │  │  │  └─ SignUpPage.tsx
│  │  │  ├─ manager/
│  │  │  │  ├─ DelegateButton.tsx
│  │  │  │  ├─ DelegateManagerPage.tsx
│  │  │  │  ├─ PendingDelegations.tsx
│  │  │  │  ├─ ReviewRequests.tsx
│  │  │  │  └─ SendDelegation.tsx
│  │  │  ├─ staff/
│  │  │  │  ├─ CreateWfhRequest.tsx
│  │  │  │  ├─ HomePage.tsx
│  │  │  │  ├─ MyWfhSchedulePage.tsx
│  │  │  │  └─ PersonalRequests.tsx
│  │  │  └─ team/
│  │  │     ├─ AllRequests.tsx
│  │  │     ├─ ApprovedTeamRequests.tsx
│  │  │     ├─ PendingRequests.tsx
│  │  │     ├─ RequestList.tsx
│  │  │     └─ TeamPage.tsx
│  │  ├─ react-app-env.d.ts
│  │  ├─ reportWebVitals.ts
│  │  ├─ router/
│  │  │  └─ Routes.tsx
│  │  ├─ setupTests.ts
│  │  ├─ theme.js
│  │  ├─ types/
│  │  │  ├─ delegation.ts
│  │  │  ├─ requests.ts
│  │  │  └─ status.ts
│  │  └─ utils/
│  │     └─ utils.ts
│  ├─ tailwind.config.js
│  └─ tsconfig.json
├─ package-lock.json
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
