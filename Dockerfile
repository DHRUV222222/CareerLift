# -------------------------------
# Base Image
# -------------------------------
FROM python:3.10-slim-bullseye

# -------------------------------
# Set working directory
# -------------------------------
WORKDIR /app

# -------------------------------
# Install system dependencies
# Needed for MySQL, Pillow and image processing
# -------------------------------
RUN apt-get update && apt-get install -y --fix-missing \
    build-essential \
    cmake \
    g++ \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    libgl1 \
    pkg-config \
    python3-dev \
    python3-distutils \
    default-libmysqlclient-dev \
    libjpeg-dev \
    zlib1g-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Upgrade pip and install Python dependencies
# -------------------------------
COPY requirements.txt /app/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install pytest pytest-cov gunicorn

# -------------------------------
# Copy project files
# -------------------------------
COPY . /app/

# -------------------------------
# Collect static files
# -------------------------------
RUN python manage.py collectstatic --noinput || true

# -------------------------------
# Expose port
# -------------------------------
EXPOSE 8000

# -------------------------------
# Production CMD
# Apply migrations and start Gunicorn
# -------------------------------
CMD ["sh", "-c", "python manage.py migrate && exec gunicorn careerlift.wsgi:application --bind 0.0.0.0:8000"]
