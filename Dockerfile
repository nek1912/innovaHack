FROM python:3.11-slim

WORKDIR /app

# Install OPA
ADD https://openpolicyagent.org/downloads/v0.68.0/opa_linux_amd64_static /usr/local/bin/opa
RUN chmod +x /usr/local/bin/opa

# Install backend dependencies
COPY backend/pyproject.toml backend/pyproject.toml
RUN pip install --no-cache-dir ./backend

# Copy backend code
COPY backend/ backend/
COPY policy/ policy/

# Run migrations and start services
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]
