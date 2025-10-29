FROM python:3.11-slim

WORKDIR /app

# Install runtime deps
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app

ENV PYTHONUNBUFFERED=1

# Default command: run the script (Render scheduled job allows overriding the command)
CMD ["python3", "post_days_remaining.py"]
