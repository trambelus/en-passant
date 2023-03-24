# Defines the ClientOptions class, which contains options for the client.
# No surprises here, just a bunch of attributes.

import logging
from typing import Any

from attrs import define
from chess import BLACK, WHITE, Color
from game import Player
from interactions import Snowflake

logger = logging.getLogger(__name__)

# TODO: handle serializable classes via a metaclass or mixin

@define
class ClientOptions:
    '''
    Contains options for the client. Serializable via to_dict() and from_dict().
    :param Player | dict[str, str] author: the author of the game
    :param Player | dict[str, str] opponent: the opponent of the game
    :param Snowflake channel_id: the Discord ID of the channel, thread, or DM in which the game is being played (must be unique among active games)
    :param int players: 1 if the game is between one player and the engine, 2 if it is between two players
    :param str notation: the notation to use for moves (options: 'san' (default), 'lan', 'uci')
    :param str ping: whether to ping each player when it is their turn (options: 'none', 'author', 'opponent', 'both')
    :param str name: the name of the game (used for the title of the thread)
    :param str engine: the name of the engine to use (options: 'maia', 'stockfish', maybe others in the future)
    :param dict engine_options: a dictionary of engine-specific options to pass to the engine (see EngineSession documentation for details)
    :param str time_control: time control to use (e.g. 5+5)
    :param bool private: whether the game is private
    '''

    author: Player | dict[str, str]
    opponent: Player | dict[str, str]
    channel_id: Snowflake | str
    players: int = 1
    notation: str = 'san'
    ping: str = 'none'
    name: str = 'Game'
    engine: str | None = None
    engine_options: dict[str, str] = {}
    time_control: str | None = None
    private: bool = False

    def __attrs_post_init__(self):
        if self.author is None:
            raise ValueError('missing required argument: author')
        if self.opponent is None and self.players == 2:
            raise ValueError('missing required argument for 2-player game: opponent')
        if self.channel_id is None:
            raise ValueError('missing required argument: channel_id')
        self.author = Player.from_dict(self.author) if isinstance(self.author, dict) else self.author
        self.opponent = Player.from_dict(self.opponent) if isinstance(self.opponent, dict) else self.opponent
    
    # Properties
    # TODO: remove unused properties
    @property
    def player(self, color: Color) -> Player:
        '''Returns the Player playing the given color.'''
        return self.author if self.author.color == color else self.opponent
    @property
    def black_player(self) -> Player:
        '''Returns the Player playing black.'''
        return self.author if self.author.color == BLACK else self.opponent
    @property
    def white_player(self) -> Player:
        '''Returns the Player playing white.'''
        return self.author if self.author.color == WHITE else self.opponent
    @property
    def ping_black(self) -> bool:
        '''Returns True if the black player should be pinged, False otherwise.'''
        return self.ping == 'both' or (self.ping == 'author' and self.author == self.black_player) or (self.ping == 'opponent' and self.opponent == self.black_player)
    @property
    def ping_white(self) -> bool:
        '''Returns True if the white player should be pinged, False otherwise.'''
        return self.ping == 'both' or (self.ping == 'author' and self.author == self.white_player) or (self.ping == 'opponent' and self.opponent == self.white_player)
    
    # Methods
    def get_ping_str(self, color: Color) -> str | None:
        '''Returns the string to use for pinging the player of the given color, or None if the player should not be pinged.'''
        if color == WHITE and self.ping_white:
            return f'<@{self.white_player.id}>'
        elif color == BLACK and self.ping_black:
            return f'<@{self.black_player.id}>'
        else:
            return None
    
    def get_id(self, color: Color) -> str:
        '''Returns the Discord ID of the player of the given color.'''
        return self.white_player.id if color == WHITE else self.black_player.id
        
    def get_nick(self, color: Color) -> str:
        '''Returns the nickname of the player of the given color.'''
        return self.white_player.nick if color == WHITE else self.black_player.nick
    
    def get_ping_or_nick(self, color: Color) -> str:
        '''Returns the string to use for pinging the player of the given color, or their nickname if they should not be pinged.'''
        ping_str = self.get_ping_str(color)
        if ping_str is None:
            return self.white_player.nick if color == WHITE else self.black_player.nick
        else:
            return ping_str

    def to_dict(self) -> dict[str, Any]:
        '''Returns a dictionary representation of the ClientOptions object.'''
        logger.debug('Converting ClientOptions object to dictionary.')
        return {
            'author': self.author.to_dict(),
            'opponent': self.opponent.to_dict(),
            'players': self.players,
            'notation': self.notation,
            'ping': self.ping,
            'channel_id': str(self.channel_id),
            'name': self.name,
            'engine': self.engine,
            'engine_options': self.engine_options,
            'time_control': self.time_control,
            'private': self.private
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> 'ClientOptions':
        '''Returns a ClientOptions object created from the given dictionary.'''
        return cls(**d)
    
    def __str__(self) -> str:
        '''Returns a string representation of the ClientOptions object.'''
        return f'ClientOptions({self.to_dict()})'
