@echo off
REM Create and activate virtual environment
echo Creating and activating virtual environment
python -m venv project_venv
call project_venv\Scripts\activate.bat

REM Install pip dependencies
echo Installing pip dependencies
pip install pre-commit black flake8

REM Install frontend dependencies
echo Installing frontend dependencies
cd frontend
npm install
cd ..

echo Setup complete. Run 'call project_venv\Scripts\activate.bat' to activate the virtual environment