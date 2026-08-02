FROM python:3.11-slim

WORKDIR /app

# Install OPA
ADD https://openpolicyagent.org/downloads/v0.68.0/opa_linux_amd64_static /usr/local/bin/opa
RUN chmod +x /usr/local/bin/opa

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy policies
COPY policy/ ./policy/

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
