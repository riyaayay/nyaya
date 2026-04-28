FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for some ML libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML artifacts and data
COPY ml/models/ /app/ml/models/
COPY ml/data/ /app/ml/data/
COPY ml/__init__.py /app/ml/
COPY ml/explainer.py /app/ml/

# Copy backend code
COPY backend/ /app/backend/

# Expose port
EXPOSE 8000

# Run FastAPI app with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
