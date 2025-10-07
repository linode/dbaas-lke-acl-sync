FROM python:3.13-slim

# Install OS dependencies
RUN apt update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy code and install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

# Entrypoint
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
