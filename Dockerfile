# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project
COPY . .

# Create directories for static and media files
RUN mkdir -p /staticfiles /mediafiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Create Gunicorn config
RUN echo "workers = 2\n\
bind = '0.0.0.0:8323'\n\
timeout = 120\n\
keepalive = 5\n\
max-requests = 0\n\
worker-class = 'gthread'\n\
threads = 2\n\
worker-connections = 1000\n\
reload = True\n\
reload_extra_files = ['/app']\n\
" > /app/gunicorn.conf.py

# Expose port
EXPOSE 8323

# Run the application with Gunicorn
CMD ["gunicorn", "--config", "/app/gunicorn.conf.py", "onevisitorbe.wsgi:application"]