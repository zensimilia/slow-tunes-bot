FROM python:3.14-slim

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

ENV UV_COMPILE_BYTECODE=1
ENV UV_SYSTEM_PYTHON=1
ENV UV_NO_SYNC=1
ENV UV_NO_DEV=1
ENV UV_NO_CACHE=1

# Copy the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Upgrade system and install dependencies
RUN echo "deb http://deb.debian.org/debian unstable main non-free contrib" >> /etc/apt/sources.list
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends sox libsox-fmt-all
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Create directories
WORKDIR /app

# Install the project's dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

# Copy the rest of the source files
COPY . .
RUN uv sync --locked

# Reset the entrypoint
ENTRYPOINT []

# Use the non-root user to run our application
RUN mkdir -p /app/data && chown -R nonroot:nonroot /app/data
USER nonroot

# Run bot
CMD ["uv", "run", "main.py"]
