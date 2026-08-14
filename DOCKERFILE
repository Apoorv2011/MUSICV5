# Use Node base and install python3
FROM node:20-bullseye

# Install python3 and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy repo
COPY . /app

# Install Python requirements if present
RUN if [ -f musicbot/requirements.txt ]; then pip3 install -r musicbot/requirements.txt; fi

# Install node dependencies for the sidecar (if package.json exists)
RUN if [ -f musicbot/jiosaavn-sidecar-clean/artifacts/api-server/package.json ]; then \
      cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server && npm ci --omit=dev; \
    fi

# If the Node sidecar needs to be built from TS sources, add build steps here
# e.g. RUN cd musicbot/jiosaavn-sidecar-clean && npm run build

ENV PORT=8080
EXPOSE 8080

# Copy start script and make executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
