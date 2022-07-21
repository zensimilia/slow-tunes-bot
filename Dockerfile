FROM python:3.10.4-alpine

# Install dependencies
RUN apk add --no-cache ffmpeg

WORKDIR /app
RUN mkdir data

# Install modules
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy files
COPY . .

# Run bot
CMD ["python", "main.py"]
