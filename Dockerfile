FROM python:3.10.4-alpine
RUN apk add --no-cache ffmpeg
RUN mkdir /app
RUN mkdir /app/data
WORKDIR /app
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY ./assets ./assets
COPY ./main.py .
COPY ./bot ./bot
ENTRYPOINT [ "python", "main.py" ]
