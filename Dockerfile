FROM python:3.14-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_COMPILE_BYTECODE=1
ENV UV_SYSTEM_PYTHON=1
ENV UV_NO_SYNC=1
ENV UV_NO_DEV=1
ENV UV_NO_CACHE=1

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy required binary from third-party images
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY --from=mwader/static-ffmpeg:latest /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:latest /ffprobe /usr/local/bin/

# Create directories
WORKDIR /app

# Install the project's dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export --frozen --no-dev --format requirements-txt -o requirements.txt \
    && uv pip install --system -r requirements.txt \
    && rm requirements.txt

# Copy the rest of the source files
COPY . .

# Reset the entrypoint
ENTRYPOINT []

# Use the non-root user to run our application
USER nonroot

# Run bot
CMD ["python", "main.py"]
