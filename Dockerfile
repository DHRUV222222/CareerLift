# --------------------------------
# Base Image
# --------------------------------
FROM python:3.10-slim

# --------------------------------
# Environment Variables
# --------------------------------
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --------------------------------
# Work Directory
# --------------------------------
WORKDIR /app

# --------------------------------
# System Dependencies (For MySQL + Pillow)
# --------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------
# Install Python Dependencies
# --------------------------------
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --------------------------------
# Copy Project Files
# --------------------------------
COPY . /app/

# --------------------------------
# Collect Static Files
# --------------------------------
RUN python manage.py collectstatic --noinput || echo "Skipping collectstatic"

# --------------------------------
# Expose Port
# --------------------------------
EXPOSE 8000

# --------------------------------
# Start Using Gunicorn
# --------------------------------
CMD ["gunicorn", "careerlift.wsgi:application", "--bind", "0.0.0.0:8000"]
