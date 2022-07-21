FROM python:3.10.4-alpine

# Install dependencies
RUN apk add --no-cache ffmpeg

# Create user and group
RUN addgroup -g 1998 botuser \
    && adduser -u 1998 -G botuser -s /bin/sh -D botuser
USER 1998

WORKDIR /app
RUN mkdir data

# Install modules
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy files
COPY --chown=1998:1998 . .

# Run bot
CMD ["python", "main.py"]
