ABOUT_TEXT = (
    "This bot is intended for personal and informational use only. "
    "For feedback or issues — contact via Telegram. Enjoy!\n\n"
    "<b>Users</b>: {users_count}\n"
    "<b>Slowed tunes</b>: {slowed_count}\n"
    "<b>Shared tunes</b>: {public_count}\n\n"
    "<b>Copyrights Notice:</b>\n"
    "All audio tracks and media files belong to their respective owners. "
    "The author of this bot does not claim any ownership "
    "or rights over the content made available through this bot.\n\n"
    "<b>DMCA / Copyright Policy:</b>\n"
    "This bot acts as a technical intermediary and does not host or store any copyrighted content on its own servers. "
    "All uploaded files are stored on Telegram servers and are downloaded by users directly from Telegram. "
    "If you are a copyright owner and believe that your rights have been infringed, please contact "
    "the developer with relevant information, and the content will be promptly reviewed and removed if necessary.\n\n"
    "<b>Terms of Use:</b>\n"
    "By using this bot, you agree that:\n"
    "— You are solely responsible for how you use the content obtained via this bot.\n"
    "— You will comply with all applicable local and international copyright laws.\n"
    "— The developer is not responsible for user actions or misuse of the bot."
)

HELP_TEXT = (
    "Send me an <code>audio file</code> or use one of the following commands:\n\n"
    "/random to get and listen shared tunes.\n"
    "/about additional info and author contacts.\n"
    "/help this help message.\n\n"
    "<b>How it works:</b>\n"
    "This bot adds a vinyl vibe to your audio by adjusting playback speed from 45 to 33 RPM. "
    "You can publish your processed tracks for other users, support their uploads with likes, "
    "or report any content that shouldn't remain publicly available."
)

START_TEXT = (
    "👋 Hello, {username}\n"
    "Send me an <code>MP3</code> file to process your audio, or try /random to discover a tracks "
    "shared by another users. Use /help to view all commands. <b>Enjoy!</b>"
)

THROTTLING_TEXT = (
    "⏳ Too many requests! Calm bro! Please <code>wait {ttl} seconds</code> before sending the same message."
)

QUEUE_POSITION_TEXT = "🕙 Added your request to the queue. Your position: {position}."

PLS_SEND_START_CMD = (
    "🤚 You must start a conversation with the bot before using it. Please send /start command to the bot."
)

FILE_IS_TOO_BIG = "💾 File is too big. Max file size is 20 MB."

START_SLOWING_DOWN = "💿 Start slowing down..."

UNSUPPORTED_FMT = "🔇 Unsupported audio format. Please check /help command."

ADMIN_RIGHTS_REQUIRED = "⛔ Nice try! You need admin rights to use this command."
