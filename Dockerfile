FROM python:3.11-slim

WORKDIR /app

# System packages
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install OPA
ADD https://openpolicyagent.org/downloads/v0.68.0/opa_linux_amd64_static /usr/local/bin/opa
RUN chmod +x /usr/local/bin/opa

# Copy backend first
COPY backend/ ./backend

# Install backend
WORKDIR /app/backend
RUN pip install --upgrade pip
RUN pip install .

# Return to workdir
WORKDIR /app

# Copy policies
COPY policy ./policy

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
