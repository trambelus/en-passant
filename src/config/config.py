# Contains the chess engine endpoint and token, discord bot info, and logging settings.
# If you want to run the engine locally, you can set the environment variables in a .env file.
# Only the environment variables required for the client end or server end need to be set on their respective machines, as specified below.
# If a required environment variable is not set, the default value will be used, and it will definitely throw an error somewhere.
# So don't do that.
# The environment variables are:
# - EP_ENGINE_USER: username to authenticate with the engine, required for both client and server ends
# - EP_ENGINE_PW: password to authenticate with the engine, required for both client and server ends
# - EP_ENGINE_HOST: the hostname to connect to the engine, only required for the client end
# - EP_ENGINE_PORT: the port to connect to the engine, required for both client and server ends
# - EP_ENGINE_EXECUTABLE: the path to the engine executable, only required for the server end
# - EP_APP_ID: the Discord app ID, only required for the client end
# - EP_APP_PUBLIC_KEY: the Discord app public key, only required for the client end
# - EP_BOT_TOKEN: the Discord bot token, only required for the client end
# - EP_HOME_GUILD_ID: the Discord guild ID of the guild where the bot stores emoji and receives admin commands, only required for the client end
# - EP_ADMIN_CHANNEL_ID: the Discord channel ID of the channel where the bot receives admin commands, only required for the client end

from dotenv import load_dotenv
import logging.config
import os
from os.path import join

# Values set from environment variables
load_dotenv()

# Required for both client and engine
ENGINE_USER = os.getenv('EP_ENGINE_USER', 'engine_user_unset')
ENGINE_PW = os.getenv('EP_ENGINE_PW', 'engine_pw_unset')
ENGINE_PORT = os.getenv('EP_ENGINE_WS_PORT', 'engine_ws_port_unset')
DB_CONNECTION_STRING = os.getenv('EP_DB_CONNECTION_STRING', 'db_connection_string_unset')

# Required only for engine
ENGINE_EXECUTABLE = os.getenv('EP_ENGINE_EXECUTABLE', 'engine_executable_unset')

# Required only for client
ENGINE_HOST = os.getenv('EP_ENGINE_HOST', '') # Can be set on server side as well, but not required. Leave blank to accept connections addressed anywhere.
APP_PUBLIC_KEY = os.getenv('EP_APP_PUBLIC_KEY', 'app_public_key_unset')
BOT_ID = os.getenv('EP_BOT_ID', 'bot_id_unset')
BOT_TOKEN = os.getenv('EP_BOT_TOKEN', 'bot_token_unset')
HOME_GUILD_ID = os.getenv('EP_HOME_GUILD_ID', 'home_guild_id_unset')
ADMIN_CHANNEL_ID = os.getenv('EP_ADMIN_CHANNEL_ID', 'admin_channel_id_unset')
# Filenames for JSON caches
ACTIVE_GAMES_CACHE_FILE = os.getenv('EP_ACTIVE_GAMES_CACHE', join('runtime-data', 'active_games.json'))
EMOJI_CACHE_FILE = os.getenv('EP_EMOJI_CACHE', join('runtime-data', 'emoji_map.json'))

# Hard-coded values
ENGINE_URL_AUTH = f'wss://{ENGINE_USER}:{ENGINE_PW}@{ENGINE_HOST}:{ENGINE_PORT}/ws'
ENGINE_URL_NOAUTH = f'ws://{ENGINE_HOST}:{ENGINE_PORT}/ws'
ENGINE_URL = ENGINE_URL_AUTH if ENGINE_USER and ENGINE_PW else ENGINE_URL_NOAUTH

DEFAULT_GAME_OPTIONS = {'variant': 'standard', 'chess960_pos': -1}
DEFAULT_ENGINE_OPTIONS = {'level': 5, 'depth': 20, 'move_time': 1000, 'engine_color': 'black', 'contempt': 0}

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'file': {  
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'EnPassant.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

logging.config.dictConfig(LOG_CONFIG)
