# slow-tunes-bot

This bot slows down an user's audio track from 45 to 33 rpm (vinyl) ratio.

## How to use

### Install

```bash
$ python -m venv env
$ source env/scripts/activate
$ pip install -r requirements
$ touch .env
```

### Configure

Paste bot's API token to `BOT_TOKEN` environment variable in `.env` file.

### Run

```bash
$ python main.py
```

## Requirements

You must install **libav** or **ffmpeg** codec.

### Linux

```bash
$ apt-get install ffmpeg libavcodec-extra
```

### Windows

1. Download and extract libav from [Windows binaries provided here](http://builds.libav.org/windows/).
2. Add the libav `/bin` folder to your PATH environment variable.

## Docker

Soon...
