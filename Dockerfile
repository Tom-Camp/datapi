FROM python:3.10

WORKDIR /app

# Install system dependencies including LevelDB
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    apt-get install -y libleveldb-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/

# Create DB directory
RUN mkdir -p /app/db

# We now need to specify the app module
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
