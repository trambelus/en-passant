from typing import Any
import logging

from chess import BLACK, WHITE, Color

from interactions import Snowflake

logger = logging.getLogger(__name__)

class ClientOptions:
    '''
    Contains options for the client. Serializable via to_dict() and from_dict().
    '''
    # TODO: handle serializable classes via a metaclass or mixin
    def __init__(self, author_id: Snowflake | str = None, opponent_id: Snowflake | str = None, author_is_white: bool = None, channel_id: Snowflake | str = None,
                 author_nick: str = None, opponent_nick: str = None, players: int = 1, notation: str = 'san',
                 ping: str = 'none', name: str = 'Game', engine: str = None, engine_options: dict[str, str] = {}, clock: bool = None, private: bool = False):
        '''
        Initialize a new ClientOptions object.
        :param Snowflake author_id: the Discord ID of the author
        :param Snowflake opponent_id: the Discord ID of the opponent (None if the opponent is the engine)
        :param bool author_is_white: whether the author is playing white (True) or black (False)
        :param Snowflake channel_id: the Discord ID of the channel, thread, or DM in which the game is being played (must be unique among active games)
        :param str author_nick: the nickname of the author (used for display purposes)
        :param str opponent_nick: the nickname of the opponent (used for display purposes)
        :param int players: 1 if the game is between one player and the engine, 2 if it is between two players
        :param str notation: the notation to use for moves (options: 'san' (default), 'lan', 'uci')
        :param str ping: whether to ping each player when it is their turn (options: 'none', 'author', 'opponent', 'both')
        :param str name: the name of the game (used for the title of the thread)
        :param str engine: the name of the engine to use (options: 'maia', 'stockfish', maybe others in the future)
        :param dict engine_options: a dictionary of engine-specific options to pass to the engine (see EngineSession documentation for details)
        :param bool clock: whether to use a clock
        :param bool private: whether the game is private
        '''
        if author_id is None:
            raise ValueError('missing required argument: author_id')
        if opponent_id is None and players == 2:
            raise ValueError('missing required argument for 2-player game: opponent_id')
        if channel_id is None:
            raise ValueError('missing required argument: channel_id')
        self.author_id: Snowflake = Snowflake(author_id)
        self.opponent_id: Snowflake = Snowflake(opponent_id)
        self.author_nick: str = author_nick
        self.opponent_nick: str = opponent_nick
        self.author_is_white: bool = author_is_white
        self.players: int = players
        self.notation: str = notation
        self.ping: str = ping
        self.channel_id: Snowflake = Snowflake(channel_id)
        self.name: str = name
        self.engine: str = engine
        self.engine_options: dict[str, str] = engine_options
        self.clock: bool = clock
        self.private: bool = private
    
    # Properties
    @property
    def black_id(self) -> str:
        '''Returns the Discord ID of the player playing black (None if the engine is playing black).'''
        return self.author_id if not self.author_is_white else self.opponent_id
    @property
    def white_id(self) -> str:
        '''Returns the Discord ID of the player playing white (None if the engine is playing white).'''
        return self.author_id if self.author_is_white else self.opponent_id
    @property
    def black_nick(self) -> str:
        '''Returns the nickname of the player playing black (None if the engine is playing black).'''
        return self.author_nick if not self.author_is_white else self.opponent_nick
    @property
    def white_nick(self) -> str:
        '''Returns the nickname of the player playing white (None if the engine is playing white).'''
        return self.author_nick if self.author_is_white else self.opponent_nick
    @property
    def ping_black(self) -> bool:
        '''Returns True if the black player should be pinged, False otherwise.'''
        return self.ping == 'both' or (self.ping == 'author' and self.author_id == self.black_id) or (self.ping == 'opponent' and self.opponent_id == self.black_id)
    @property
    def ping_white(self) -> bool:
        '''Returns True if the white player should be pinged, False otherwise.'''
        return self.ping == 'both' or (self.ping == 'author' and self.author_id == self.white_id) or (self.ping == 'opponent' and self.opponent_id == self.white_id)
    
    # Methods
    def get_ping_str(self, color: Color) -> str | None:
        '''Returns the string to use for pinging the player of the given color, or None if the player should not be pinged.'''
        if color == WHITE and self.ping_white:
            return f'<@{self.white_id}>'
        elif color == BLACK and self.ping_black:
            return f'<@{self.black_id}>'
        else:
            return None

    def to_dict(self) -> dict[str, Any]:
        '''Returns a dictionary representation of the ClientOptions object.'''
        logger.debug('Converting ClientOptions object to dictionary.')
        return {
            'author_id': str(self.author_id),
            'opponent_id': str(self.opponent_id),
            'author_nick': self.author_nick,
            'opponent_nick': self.opponent_nick,
            'author_is_white': self.author_is_white,
            'players': self.players,
            'notation': self.notation,
            'ping': self.ping,
            'channel_id': str(self.channel_id),
            'name': self.name,
            'engine': self.engine,
            'engine_options': self.engine_options,
            'clock': self.clock,
            'private': self.private
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> 'ClientOptions':
        '''Returns a ClientOptions object created from the given dictionary.'''
        return cls(**d)
    
    def __str__(self) -> str:
        '''Returns a string representation of the ClientOptions object.'''
        return f'ClientOptions({self.to_dict()})'
