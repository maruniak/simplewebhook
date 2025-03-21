# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the index.html file
COPY index.html /app/index.html

# Copy the .env file
COPY .env /app/.env

# Copy the certificate and key files
COPY pem /app/pem

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "40871"]
