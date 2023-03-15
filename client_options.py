import interactions

class ClientOptions:
    '''
    Contains options for the client.
    '''
    def __init__(self, author: interactions.Member = None, opponent: interactions.Member = None, author_is_white: bool = None, channel_id: str = None,
                 author_nick: str = None, opponent_nick: str = None, players: int = 1, notation: str = 'san',
                 ping: str = 'none', name: str = 'Game', engine: str = None, engine_options: dict = {}, clock: bool = None, private: bool = False):
        '''
        Initialize a new ClientOptions object.
        :param interactions.Member author: Member object representing the author of the command
        :param interactions.Member opponent: Member object representing the opponent (None if the opponent is the engine)
        :param bool author_is_white: whether the author is playing white (True) or black (False)
        :param str channel_id: the Discord ID of the channel, thread, or DM in which the game is being played (must be unique among active games)
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
        if author is None:
            raise ValueError('missing required argument: author')
        if opponent is None and players == 2:
            raise ValueError('missing required argument: opponent')
        if channel_id is None:
            raise ValueError('missing required argument: channel_id')
        self.author = author
        self.opponent = opponent if opponent else {'id': None, 'nick': None}
        self.author_nick = author_nick
        self.opponent_nick = opponent_nick
        self.author_is_white = author_is_white
        self.players = players
        self.notation = notation
        self.ping = ping
        self.channel_id = channel_id
        self.name = name
        self.engine = engine
        self.engine_options = engine_options
        self.clock = clock
        self.private = private
    
    # Properties
    @property
    def black_id(self):
        '''Returns the Discord ID of the player playing black (None if the engine is playing black).'''
        return self.author.id if not self.author_is_white else self.opponent.id
    @property
    def white_id(self):
        '''Returns the Discord ID of the player playing white (None if the engine is playing white).'''
        return self.author.id if self.author_is_white else self.opponent.id
    @property
    def black_nick(self):
        '''Returns the nickname of the player playing black (None if the engine is playing black).'''
        return self.author_nick if not self.author_is_white else self.opponent_nick
    @property
    def white_nick(self):
        '''Returns the nickname of the player playing white (None if the engine is playing white).'''
        return self.author_nick if self.author_is_white else self.opponent_nick
    @property
    def ping_black(self):
        '''Returns True if the black player should be pinged, False otherwise.'''
        return self.ping == 'both' or (self.ping == 'author' and self.author.id == self.black_id) or (self.ping == 'opponent' and self.opponent_id == self.black_id)
    @property
    def ping_white(self):
        '''Returns True if the white player should be pinged, False otherwise.'''
        return self.ping == 'both' or (self.ping == 'author' and self.author.id == self.white_id) or (self.ping == 'opponent' and self.opponent_id == self.white_id)