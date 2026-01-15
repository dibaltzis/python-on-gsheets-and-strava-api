# Use lightweight Python base image for ARM & AMD64
FROM python:3.13-slim

# Set environment to avoid Python buffering issues
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install dependencies for building Python packages (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
        cron \
        build-essential \
        ca-certificates \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source code
COPY src/ /app/src/
COPY requirements.txt /app/

ARG VERSION
LABEL build.version="${VERSION}"
ENV APP_VERSION="${VERSION}"

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Environment variable that user provides in docker-compose:
ENV CRON_SCHEDULE="0 5 * * *"

# Add the script that creates cron job dynamically
COPY cron-run.sh /app/cron-run.sh
RUN chmod +x /app/cron-run.sh

# The entrypoint creates the cron file and runs cron in foreground
ENTRYPOINT ["/app/cron-run.sh"]