# Maintains set of active game sessions and handles Discord interactions

import json
import logging
import sys
from pprint import pformat

import interactions
from interactions import Intents
from interactions.utils.get import get

import client_session
from admin_commands import refresh_emoji_names, register_admin_commands
from config import BOT_TOKEN, HOME_GUILD_ID, EMOJI_CACHE_FILE
from game_commands import register_game_commands
from game_manager import load_active_games

# TODO:
# - Add support for resuming games (e.g. if the bot restarts)
#     - For now, include support for resuming from FEN string or moves list, but when the bot is more robust, rely on saved game state
#     - Save game options (e.g. time control, increment, etc.) in the game session
# - Also persist game options per user, e.g. level, time control, etc.
# - Allow using pvs instead of bestmove when the engine is responding slowly or time is low
# - Add game timers
# - Add non-game commands (e.g. help, stats, rankings, etc.)
# - Use human-readable session IDs instead of UUIDs (proquints? NATO phonetic alphabet?)
# - Add command for spectating games in a private thread with engine-supplied analysis
#     - Web-based UI for spectating games? Stretch goal.
#     - Can GPT-3 be used to generate analysis?
# - Add support for zero-player games (AI vs AI)
# - Add puzzles (lichess?)
# - Add support for multiple engines (stockfish, maia, leela, etc.)
# - Support engine info arriving asynchronously, not in response to a request (better moves when given time to think)]
# Commands to add:
# - /again command to play the same game again (same options, color, opponent, etc.)
# - /undo command to undo the last move
# - /resign command to resign the game
# - /draw command to offer a draw
# - /accept command to accept a draw or undo request
# - /decline command to decline a draw or undo request

logger = logging.getLogger(__name__)

# TODO: figure out what file to put this in; it doesn't seem to belong anywhere in particular
# Probably the serializer module, when I get around to writing it (PersistenceManager? PersistenceService?)
def load_emoji_names() -> dict[str, str]:
    '''Load the emoji names from the emoji_map JSON file'''
    # Open the emoji_map JSON file
    try:
        with open(EMOJI_CACHE_FILE, 'r') as f:
            # Load the JSON file
            emoji_map = json.load(f)
            logger.info('Emoji map loaded from file')
            return emoji_map
    except FileNotFoundError:
        # If the file does not exist, return None so the calling function can create it via refresh_emoji_names
        logger.warning('Emoji map file not found; querying Discord API for emoji IDs')
        return None

def main():
    # Load the active games into the game manager
    load_active_games()
    # client = interactions.Client(token=BOT_TOKEN, intents=Intents.DEFAULT | Intents.GUILD_MESSAGE_CONTENT)
    # It seems like GUILD_MESSAGE_CONTENT isn't required to pick up relevant THREAD_CREATED events, so we'll leave it out for now
    client = interactions.Client(token=BOT_TOKEN, intents=Intents.DEFAULT)
    register_admin_commands(client)
    register_game_commands(client)

    @client.event
    async def on_ready():
        logger.debug('\\/' * 50)
        logger.info('Bot is ready')
        logger.debug('/\\' * 50)
        # Attempt to load the emoji names from the JSON file, and if that fails, refresh them from the Discord API
        emoji_map = load_emoji_names() or await refresh_emoji_names(client)
        if not emoji_map:
            logger.error('Failed to load emoji names from Discord API; board display will not work')
            logger.error('Exiting...')
            sys.exit(1)
        client_session.populate_emoji_map(emoji_map)
        
    # Run the bot
    try:
        client.start()
    except KeyboardInterrupt:
        logger.info('Exiting...')
        sys.exit(0)

if __name__ == '__main__':
    main()