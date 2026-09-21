FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if any are needed for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install project dependencies
COPY pyproject.toml .
# We use pip to install the project and its dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Ensure unbuffered output for logs
ENV PYTHONUNBUFFERED=1

# Command to run the bot
CMD ["python", "-m", "discord_insta.main"]
