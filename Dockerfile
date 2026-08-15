FROM node:22-bookworm

# Install python + build deps needed for pip wheels and general builds
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv build-essential python3-dev libffi-dev libssl-dev zip unzip ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy repository into image
COPY . /app

# Enable corepack and activate pnpm v9 (prevents pnpm 11 build script restrictions)
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate

# Install Node workspace deps at repo root using pnpm
RUN if [ -f pnpm-workspace.yaml ] || [ -f package.json ]; then \
      pnpm install --no-frozen-lockfile || pnpm install --shamefully-hoist; \
    fi

# Build the sidecar package
RUN if [ -f musicbot/jiosaavn-sidecar-clean/artifacts/api-server/package.json ]; then \
      cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server && \
      pnpm run build || (echo "== sidecar build failed: see pnpm output above ==" && exit 1); \
    fi

# Install Python deps
RUN if [ -f musicbot/pyproject.toml ]; then \
      pip3 install --no-cache-dir --break-system-packages ./musicbot; \
    elif [ -f musicbot/requirements.txt ]; then \
      pip3 install --no-cache-dir --break-system-packages -r musicbot/requirements.txt; \
    fi

# Ensure start script is present and executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV PORT=8080
EXPOSE 8080

CMD ["/start.sh"]
