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

Set the necessary environment variables from table below or fill they in `.env` file. Available environment variables to configure the Bot:

Variable| Type | Description | Required
--- | --- | --- | ---
`ADMIN_ID` | integer | Telegram _user_id_ of moderator/administrator. | *
`ALBUM_ART` | string | Relative path to album art (cover) JPEG image file. |
`BOT_TOKEN` | string | Telegram API Bot token. | *
`DATA_DIR` | string | Relative path to the directory where the Bot will store a data. |
`DB_FILE` | string | SQLite database filename. |
`DEBUG` | boolean | If true change logging level to _debug_. |
`SPEED_RATIO` | float | What slowing ratio to use. 1 - original speed, 0.5 - half speed, etc. |
`REDIS_HOST` | string | Host or IP-address of Redis server. |
`REDIS_PORT` | integer | Port of Redis server. |
`THROTTLE_RATE` | integer | Throttling rate in seconds. |

### Run

```bash
$ python main.py
```

## Requirements

1. [Redis](https://redis.io/) server.
2. You must install **libav** or **ffmpeg** codec.

    ### Linux

    ```bash
    $ apt-get install ffmpeg libavcodec-extra
    ```

    ### Windows

    * Download and extract libav from [Windows binaries provided here](http://builds.libav.org/windows/).
    * Add the libav `/bin` folder to your PATH environment variable.

## Docker

```bash
$ docker-compose up -d
```
