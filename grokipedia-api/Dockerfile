# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the local Grokipedia SDK and install it
COPY ./grokipedia-sdk /app/grokipedia-sdk
RUN pip install --no-cache-dir -e /app/grokipedia-sdk

# Copy the main API file
COPY main.py .

# Railway provides the PORT environment variable
# We default to 8000 if it's not set
ENV PORT=${PORT:-8000}

# Expose the port the app runs on
EXPOSE $PORT

# Command to run the application using Uvicorn
# This will be picked up by Railway
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

