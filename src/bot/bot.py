# Maintains set of active game sessions and handles Discord interactions

import json
import logging
import sys
from pprint import pformat

import interactions
from interactions import Intents

from client import populate_emoji_map, load_active_games
from commands import register_commands, refresh_emoji_names
from config import BOT_TOKEN, EMOJI_CACHE_FILE

# TODO:
# - Look into multiprocessing to speed up the bot
# - Switch to using a database instead of JSON files (i.e. MongoDB)
# - Add support for resuming games (e.g. if the bot restarts)
#     - For now, include support for resuming from FEN string or moves list, but when the bot is more robust, rely on saved game state
#     - Save game options (e.g. time control, increment, etc.) in the game session
# - Also persist game options per user, e.g. level, time control, etc.
# - Allow using pvs instead of bestmove when the engine is responding slowly or time is low
# - Add game timers
# - Add non-game commands (e.g. help, stats, rankings, etc.)
# - Add command for spectating games in a private thread with engine-supplied analysis
#     - Web-based UI for spectating games? Stretch goal.
#     - Can GPT-3 be used to generate analysis?
# - Investigate using buttons for moves instead of text commands
# - Overhaul message format to use embeds
# - Add support for zero-player games (AI vs AI)
# - Add puzzles (lichess?)
# - Add support for multiple engines (stockfish, maia, leela, etc.)
# - Support engine info arriving asynchronously, not in response to a request (better moves when given time to think)
# - Fog of war (hide opponent's pieces) - use ephemeral messages? /peek command?
# - Isolate all string literals into a separate file
# Commands to add:
# - /again command to play the same game again (same options, color, opponent, etc.)
# - /undo command to (request to) undo the last move
# - /resign command to resign the game
# - /draw command to offer a draw
# Commands to update:
# - /moves:
#     - If there are more than 25 legal moves, show the first 25 and prompt the user to use /moves to see the rest
#     - If the user clicks a move from a previous /moves command that's no longer valid, show an error message

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

def run():
    # Load the active games into the game manager
    load_active_games()
    # client = interactions.Client(token=BOT_TOKEN, intents=Intents.DEFAULT | Intents.GUILD_MESSAGE_CONTENT)
    # It seems like GUILD_MESSAGE_CONTENT isn't required to pick up relevant THREAD_CREATED events, so we'll leave it out for now
    bot = interactions.Client(token=BOT_TOKEN, intents=Intents.DEFAULT)
    register_commands(bot)

    @bot.event
    async def on_ready():
        logger.debug('\\/' * 50)
        logger.info('Bot is ready')
        logger.debug('/\\' * 50)
        # Attempt to load the emoji names from the JSON file, and if that fails, refresh them from the Discord API
        emoji_map = load_emoji_names() or await refresh_emoji_names(bot)
        if not emoji_map:
            logger.error('Failed to load emoji names from Discord API; board display will not work')
            logger.error('Exiting...')
            sys.exit(1)
        populate_emoji_map(emoji_map)
        
    # Run the bot
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info('Exiting...')
        sys.exit(0)

if __name__ == '__main__':
    run()