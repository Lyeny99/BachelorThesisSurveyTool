FROM ubuntu:latest
LABEL authors="christina"

ENTRYPOINT ["top", "-b"]

# Use the official Python 3.11 Docker base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file (if exists) and application code
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir gunicorn

RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY . .

# Expose the application port
EXPOSE 8000

# Set environment variable to disable buffering, useful for logging
ENV PYTHONUNBUFFERED=1

# Run the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
