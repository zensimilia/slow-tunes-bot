# slow-tunes-bot

This bot slows down an user's audio from 45 to 33 rpm (vinyl) ratio.
Protected from throttling. Queue implemented. Supports webhook
and polling modes.

## How to use

### Docker: the easiest way

```bash
touch .env
docker-compose up -d --build
```

### Install: old method

```bash
python -m venv env
source env/scripts/activate
pip install -r requirements
touch .env
python main.py
```

## Configure

Set the necessary environment variables from table below or fill they in `.env` file. Available environment variables to configure the Bot:

| Variable        | Type    | Description                                                           | Required |
| --------------- | ------- | --------------------------------------------------------------------- | -------- |
| `ADMIN_ID`      | integer | Telegram _user_id_ of moderator/administrator.                        | \*       |
| `ALBUM_ART`     | string  | Relative path to album art (cover) JPEG image file.                   |
| `APP_HOST`      | string  | Host that bot will listen on.                                         |
| `APP_PORT`      | integer | Port that bot will listen on.                                         |
| `BOT_TOKEN`     | string  | Telegram API Bot token.                                               | \*       |
| `DATA_DIR`      | string  | Relative path to the directory where the Bot will store a data.       |
| `DB_FILE`       | string  | SQLite database filename.                                             |
| `DEBUG`         | boolean | If true change logging level to _debug_.                              |
| `SPEED_RATIO`   | float   | What slowing ratio to use. 1 - original speed, 0.5 - half speed, etc. |
| `REDIS_HOST`    | string  | Host or IP-address of Redis server.                                   |
| `REDIS_PORT`    | integer | Port of Redis server.                                                 |
| `TASK_LIMIT`    | integer | Queue limit for single user tasks.                                    |
| `THROTTLE_RATE` | integer | Throttling rate in seconds.                                           |
| `USE_WEBHOOK`   | boolean | If true use webhook else polling. Default false.                      |
| `WEBHOOK_HOST`  | string  | Webhook host for receive Telegram updates (eg. "mywebhook.com").      |
| `WEBHOOK_PATH`  | string  | Webhook path (eg. "/bot/").                                           |

## Requirements

The following requirements are not needful if you are using Docker.

1. [Redis](https://redis.io/) server.
2. You must install _libav_ or _ffmpeg_ codec.

    **Linux:**

    ```bash
    apt-get install ffmpeg libavcodec-extra
    ```

    **Windows:**

    - Download and extract libav from [Windows binaries provided here](http://builds.libav.org/windows/).
    - Add the libav `/bin` folder to your PATH environment variable.
