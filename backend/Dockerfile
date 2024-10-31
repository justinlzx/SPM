# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

# Install Watchfiles for improved file watching
# RUN pip install watchfiles

# Copy the rest of the application code
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI application with uvicorn and watchfiles
# CMD ["watchfiles", "--filter", "python", "uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload"]
CMD ["python", "main.py"]