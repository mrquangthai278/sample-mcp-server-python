# Use Python 3.10 as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create non-root user for better security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose port 2025
EXPOSE 2025

# Command to run the application
CMD ["python", "-c", "import server; import uvicorn; \
     server.app.debug = False; \
     uvicorn.run(server.app, host='0.0.0.0', port=2025)"]