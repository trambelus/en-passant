# Waits to receive messages from the client component, and manages the engine sessions.

import logging
from attrs import define

logger = logging.getLogger(__name__)

from .engine_session import EngineSession

@define
class Variation:
    '''Represents a principal variation.'''
    moves: list[str]
    score: int
    mate: int | None = None

@define
class MoveRequest:
    '''Represents a message containing a move from the client component.'''
    id: str
    starting_fen: str | None = None
    moves: list[str]
    multipv: int = 1

@define
class MoveResponse:
    '''Represents a message containing a move from the engine component.'''
    id: str
    bestmove: str
    ponder: str | None = None
    pvs: list[Variation] = []


@define
class EngineSessionManager:
    '''
    Manages the engine sessions.
    '''
    sessions: dict[str, EngineSession] = {}

    def __getitem__(self, key: str) -> EngineSession:
        '''Returns the EngineSession with the given key.'''
        return self.sessions[key]
    
    def __setitem__(self, key: str, value: EngineSession):
        '''Sets the EngineSession with the given key.'''
        self.sessions[key] = value

    def __delitem__(self, key: str):
        '''Deletes the EngineSession with the given key.'''
        del self.sessions[key]

    def __contains__(self, key: str) -> bool:
        '''Returns whether the EngineSession with the given key exists.'''
        return key in self.sessions


def run():
    logger.info("Starting En Passant Engine...")
    pass # TODO: implement

if __name__ == '__main__':
    run()
