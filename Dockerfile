FROM node:20-bullseye

# Install python3 and system build dependencies needed to build wheels
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv build-essential python3-dev libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy repository
COPY . /app

# Install Python deps (try pyproject.toml first or requirements.txt). Allow failures to continue.
RUN if [ -f musicbot/pyproject.toml ]; then \
      pip3 install --no-cache-dir ./musicbot || true; \
    elif [ -f musicbot/requirements.txt ]; then \
      pip3 install --no-cache-dir -r musicbot/requirements.txt || true; \
    fi

# Install and build JioSaavn sidecar: try npm ci, but fall back to npm install if no lockfile
RUN if [ -f musicbot/jiosaavn-sidecar-clean/artifacts/api-server/package.json ]; then \
      cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server && \
      npm ci --omit=dev || npm install --omit=dev && \
      npm run build || true; \
    fi

ENV PORT=8080
EXPOSE 8080

# Copy start script and make executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
