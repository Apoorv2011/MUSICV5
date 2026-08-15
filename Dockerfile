FROM node:22-bookworm

# Install system dependencies (ffmpeg, python, curl, build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv build-essential python3-dev libffi-dev libssl-dev zip unzip ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv globally
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy repository into image
COPY . /app

# Enable corepack and activate pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Build workspace sidecar safely
RUN if [ -f pnpm-workspace.yaml ] || [ -f package.json ]; then \
      pnpm install --no-frozen-lockfile || pnpm install --shamefully-hoist || true; \
    fi

RUN if [ -f musicbot/jiosaavn-sidecar-clean/artifacts/api-server/package.json ]; then \
      cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server && \
      (pnpm install --no-frozen-lockfile || npm install --legacy-peer-deps || true) && \
      (pnpm run build || node ./build.mjs || true); \
    fi

# Parse pyproject.toml dependencies directly and install via pip
RUN python3 -c "import tomllib; f=open('musicbot/pyproject.toml','rb'); d=tomllib.load(f); deps=d.get('project',{}).get('dependencies',[]); f.close(); open('/tmp/reqs.txt','w').write('\n'.join(deps))" && \
    pip3 install --no-cache-dir --break-system-packages -r /tmp/reqs.txt

# Setup start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV PORT=8080
EXPOSE 8080

CMD ["/start.sh"]
