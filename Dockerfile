FROM node:20-bullseye

# Install python3 and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy repository
COPY . /app

# Install Python deps (try to install package from pyproject; fallback to requirements.txt if present)
RUN if [ -f musicbot/pyproject.toml ]; then \
      pip3 install --no-cache-dir ./musicbot || true; \
    elif [ -f musicbot/requirements.txt ]; then \
      pip3 install --no-cache-dir -r musicbot/requirements.txt; \
    fi

# Build/install the JioSaavn sidecar if it needs building
RUN if [ -f musicbot/jiosaavn-sidecar-clean/artifacts/api-server/package.json ]; then \
      cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server && \
      npm ci --omit=dev && \
      npm run build || true; \
    fi

ENV PORT=8080
EXPOSE 8080

# Ensure start.sh is present and executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
