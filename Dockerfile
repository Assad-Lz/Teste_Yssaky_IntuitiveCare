# Dockerfile (Root - Backend)
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code
COPY . .

# Expose port 8000
EXPOSE 8000

# Command to start
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]