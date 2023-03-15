# Maintains set of active game sessions and handles Discord interactions

import asyncio
import json
import logging
import sys
from pprint import pformat
from typing import Dict, List

import chess
import interactions
import websockets

import client_session
from admin_commands import refresh_emoji_names, register_admin_commands
from client_session import board_to_emoji
from command_defs import commands
from config import BOT_TOKEN, HOME_GUILD_ID
from game_commands import register_game_commands

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
# - Support engine info arriving asynchronously, not in response to a request (better moves when given time to think)

logger = logging.getLogger(__name__)

# TODO: figure out what file to put this in; it doesn't seem to belong anywhere in particular
def load_emoji_names() -> Dict[str, str]:
    '''Load the emoji names from the emoji_map JSON file'''
    # Open the emoji_map JSON file
    try:
        with open('emoji_map.json', 'r') as f:
            # Load the JSON file
            emoji_map = json.load(f)
            logger.info('Emoji map loaded from file')
            return emoji_map
    except FileNotFoundError:
        # If the file does not exist, return None so the calling function can create it via refresh_emoji_names
        logger.warning('Emoji map file not found; querying Discord API for emoji IDs')
        return None

def save_active_games(active_games: Dict[str, client_session.ClientGameSession]):
    '''Save the active games to a JSON file'''
    # Open the active_games JSON file
    with open('active_games.json', 'w') as f:
        # Save the active games to the JSON file
        json.dump({k: v.to_json() for k, v in active_games}, f, indent=4, default=lambda o: o.__dict__)

def load_active_games() -> Dict[str, client_session.ClientGameSession]:
    '''Load the active games from the active_games JSON file'''
    try:
        # Open the active_games JSON file
        with open('active_games.json', 'r') as f:
            # Load the JSON file
            active_games = json.load(f)
            # Convert the JSON objects to ClientGameSession objects
            for game_id, game in active_games.items():
                active_games[game_id] = client_session.ClientGameSession.from_json(game)
            logger.info('Active games loaded from file')
            return active_games
    except FileNotFoundError:
        # If the file does not exist, return an empty dict
        logger.warning('Active games file not found; starting with no active games')
        return {}

def main():
    # Load the active games from the JSON file
    active_games = load_active_games()
    client = interactions.Client(token=BOT_TOKEN)
    register_admin_commands(client)
    register_game_commands(client, active_games)

    @client.event
    async def on_ready():
        logger.info('Bot is ready')
        # Attempt to load the emoji names from the JSON file, and if that fails, refresh them from the Discord API
        emoji_map = load_emoji_names() or await refresh_emoji_names(client)
        if not emoji_map:
            logger.error('Failed to load emoji names from Discord API; board display will not work')
            logger.error('Exiting...')
            sys.exit(1)
        client_session.populate_emoji_map(emoji_map)

    @client.command(
        name=commands['admin_commands']['ping']['name'],
        description=commands['admin_commands']['ping']['description'],
        scope=commands['admin_commands']['GUILD_ID']
    )
    async def show_board(ctx: interactions.CommandContext):
        response_str = 'Pong! \n' + board_to_emoji(chess.Board())
        await ctx.send(content=response_str)
        
    # Run the bot
    try:
        client.start()
    except KeyboardInterrupt:
        logger.info('Exiting...')
        sys.exit(0)

if __name__ == '__main__':
    main()