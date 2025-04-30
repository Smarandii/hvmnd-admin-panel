# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Keep Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure output is immediately flushed to the terminal
ENV PYTHONUNBUFFERED 1

# Install system dependencies (for psycopg2 and others if needed)
RUN apt-get update \
    && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

EXPOSE 9875

CMD ["gunicorn", "--bind", "0.0.0.0:9875", "run:app"]
