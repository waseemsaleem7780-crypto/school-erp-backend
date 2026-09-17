FROM python:3.11-slim

# Install PostgreSQL client (pg_dump)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose port
EXPOSE 8080

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
