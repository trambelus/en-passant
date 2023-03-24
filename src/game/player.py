from attrs import define
from typing import Any, Literal
from chess import BLACK, WHITE, Color

@define
class PlayerOptions:
    '''
    Contains options for a player. Serializable via to_dict() and from_dict().
    This class is intended to eventually be used for storing player preferences in a database.
    :param bool ping: whether to ping the player when it is their turn (True) or not (False)
    :param str notation: the notation to use for the player (SAN or UCI, maybe more later)
    :param bool flip: whether to flip the board for the player when they are playing black (True) or not (False)
    :param bool default_ranked: whether to default to ranked games for the player (True) or not (False)
    :param str default_time: the default time control for the player (e.g. '5+0')
    '''
    ping: bool = False
    notation: Literal['san', 'uci'] = 'san'
    flip: bool = False
    default_ranked: bool = True
    default_time: str | None = None

@define
class Player:
    '''
    Represents a player in a game. Serializable via to_dict() and from_dict().
    :param str id: the ID of the player, used to uniquely identify them (None if the player is the engine)
    :param str nick: the nickname of the player (used for display purposes)
    :param Color color: the color the player is playing (WHITE or BLACK)
    :param bool engine: whether the player is the engine (True) or a human (False)
    '''
    # ID would be a Snowflake, but we need to be able to serialize it easily to JSON,
    # and it's best to avoid a dependency on the interactions library in this module.
    id: str | int | None
    nick: str | None
    color: Color
    engine: bool = False

    def __attrs_post_init__(self) -> None:
        # Validate attributes
        if not self.engine:
            if self.id is None:
                raise ValueError('id must be set for human players')
            if self.nick is None:
                raise ValueError('nick must be set for human players')
        else:
            if self.nick is None:
                self.nick = 'En Passant'
        self.id = str(self.id) if self.id is not None else None
        self.color = Color(self.color)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'nick': self.nick,
            'color': str(self.color),
            'engine': self.engine
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Player':
        return cls(
            id=data['id'],
            nick=data['nick'],
            color=Color(data['color']),
            engine=data['engine']
        )
