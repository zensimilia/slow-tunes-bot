FROM python:3.10.4-slim

# Upgrade and install dependencies
# RUN apt-get update && apt-get upgrade
RUN echo "deb http://deb.debian.org/debian unstable main non-free contrib" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y --no-install-recommends sox libsox-fmt-all

WORKDIR /app
RUN mkdir data

# Install modules
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy files
COPY . .

# Clean
RUN rm -v requirements.txt
RUN rm -rf /var/lib/apt/lists/*

# Run bot
CMD ["python", "main.py"]
