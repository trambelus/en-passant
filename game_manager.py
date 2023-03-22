# game_manager.py
# This used to be a dict, active_games, passed around all over the place, but now it's a singleton class.
# Access the singleton instance of GameManager with game_manager.
# Also supports serialization to JSON and loading from JSON.
# Maybe there'll be some serialization manager later on, but for now, GameManager will handle it.

import json
import logging
import datetime
import re

from interactions import Snowflake

from client_session import ClientGameSession
from config import ACTIVE_GAMES_CACHE_FILE

logger = logging.getLogger(__name__)

'''
Notes to self on serialization pipeline, just to lay it all out:
- new_game calls GameManager.add_game()
- GameManager.add_game() is decorated with validate_discord_snowflake() (should work now)
- new_game is decorated with save_after()
- save_after() calls GameManager.to_dict()

'''

class GameManager:
    '''
    Singleton class to manage the active games.
    Stores the active games in a dict, where the keys are the game IDs and the values are the ClientGameSession objects.
    Serializes itself to JSON and loads itself from JSON.
    '''
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance: GameManager = super(GameManager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._active_games: dict[str, ClientGameSession] = {}

    def __len__(self) -> int:
        '''Get the number of active games.'''
        return len(self._active_games)
    
    def __iter__(self):
        '''Get an iterator for the active games.'''
        return iter(self._active_games)
    
    def __getitem__(self, key: int | str | Snowflake):
        '''Get a game from the active games.'''
        key = str(key)
        return self._active_games[key]
    
    def __setitem__(self, key: int | str | Snowflake, value: ClientGameSession):
        '''Set a game in the active games.'''
        key = str(key)
        self._active_games[key] = value

    def __delitem__(self, key: int | str | Snowflake):
        '''Delete a game from the active games.'''
        key = str(key)
        del self._active_games[key]
    
    def __contains__(self, key: int | str | Snowflake):
        '''Check if a game is in the active games.'''
        key = str(key)
        return key in self._active_games
    
    def __repr__(self):
        '''Get a string representation of the active games.'''
        return f'GameManager(active_games={self._active_games}))'

    def __str__(self):
        return self.__repr__()

    def add_game(self, game_id: int | str | Snowflake, game_session: ClientGameSession):
        '''Add a game to the active games. If the game already exists, it will be overwritten. Also saves the active games to a JSON file.'''
        self[game_id] = game_session
        save_active_games()

    def remove_game(self, game_id: str):
        '''Remove a game from the active games. Also saves the active games to a JSON file.'''
        del self[game_id]
        save_active_games()

    def to_dict(self) -> dict[str, dict[str, ClientGameSession]]:
        '''Convert the active games to a dict'''
        return {k: v.to_dict() for k, v in self._active_games.items()}
    
# Get the singleton instance of GameManager
game_manager = GameManager()

def save_after(func):
    '''Decorator to add a task to save the active games to a JSON file after the decorated coroutine is called.'''
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        save_active_games()
        return result
    return wrapper

def save_active_games():
    '''Save the active games to a JSON file'''
    # Open the active_games JSON file
    with open(ACTIVE_GAMES_CACHE_FILE, 'w') as f:
        # Save the active games to the JSON file
        try:
            json.dump(game_manager.to_dict(), f, indent=4)
            logger.info('Active games saved to file')
        except Exception as e:
            logger.error(f'Could not save active games to file: {e}')
            logger.exception(e)

def load_active_games() -> bool:
    '''Load the active games from the active_games JSON file'''
    try:
        # Open the active_games JSON file
        with open(ACTIVE_GAMES_CACHE_FILE, 'r') as f:

            # Load the JSON file
            try:
                active_games = json.load(f)
            except json.decoder.JSONDecodeError:
                # If the JSON file is empty (or invalid), return False so the calling function can create it
                logger.warning('Could not load active games from file; starting with no active games')
                return False
            
            # Convert the JSON objects to ClientGameSession objects
            for game_id_str, game_dict in active_games.items():
                active_games[Snowflake(game_id_str)] = ClientGameSession.from_dict(game_dict)
            logger.info('Active games loaded from file')

            # Set the active games to the loaded active games
            game_manager._active_games = active_games
            return True
        
    except FileNotFoundError:
        # If the file does not exist, return False so the calling function can create it
        logger.warning('Active games file not found; starting with no active games')
        return False
