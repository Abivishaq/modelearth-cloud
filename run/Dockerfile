FROM python:3.9-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080

# Run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app