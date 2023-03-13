FROM python:3.10.4-alpine

# Upgrade and install dependencies
RUN apk update && apk upgrade
RUN apk add ffmpeg

WORKDIR /app
RUN mkdir data

# Install modules
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy files
COPY . .

# Clean
RUN rm -v requirements.txt
RUN rm -vrf /var/cache/apk/*

# Run bot
CMD ["python", "main.py"]
