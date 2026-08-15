FROM node:22-bookworm

# Install system dependencies (ffmpeg, python, curl, build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv build-essential python3-dev libffi-dev libssl-dev zip unzip ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv globally (astral.sh)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy repository content into image
COPY . /app

# Enable corepack and prepare pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Install all workspace dependencies using pnpm at the root
RUN pnpm install --no-frozen-lockfile || pnpm install --shamefully-hoist

# Build all workspace packages (including sidecar/api-server)
RUN pnpm run build || (cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server && pnpm run build)

# Install Python dependencies using uv inside musicbot folder
RUN cd musicbot && uv sync --frozen || uv pip install --system -r <(uv pip compile pyproject.toml 2>/dev/null) || pip3 install --no-cache-dir --break-system-packages . --no-build-isolation || true

# Prepare start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV PORT=8080
EXPOSE 8080

CMD ["/start.sh"]
