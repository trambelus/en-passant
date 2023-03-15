# Extends GameSession to manage an engine process for each session and to provide a method to get the best move and principal variations.
# Also provides websocket server functionality to communicate with the client.
# The client should send a JSON object with the following fields:
# - type: 'new', 'resume', 'move', 'undo', or 'exit'
# - game_options: a JSON object, only required for 'new' requests, with the following fields:
#   - variant: the variant to play
#   - chess960_pos: the chess960 starting position to use, if any, or -1 for standard chess
#   - level: the level to play at, defaults to 5
#   - depth: the depth to search to, defaults to 20
#   - move_time: the time to search for each move, in milliseconds, defaults to 1000
#   - engine_color: the color the engine will play as, defaults to 'black'
#   - contempt: the contempt value to use, defaults to 0
# - session_id: the session ID to resume, only required for 'resume' requests
# - move: the move to make, only required for 'move' requests
# - undo: the number of moves to undo, optional for 'undo' requests, defaults to 1
#
# The engine will respond with a JSON object with the following fields:
# - type: same as the request type
# - session_id: the session ID, only included for 'new' responses
# - move: the best move, only included for 'move' responses
# - pvs: list of principal variations, only included for 'move' responses
# - code: the response or error code (e.g. 200, 400, 500)
# - message: the response or error message (e.g. 'OK', 'Invalid move', 'Illegal move', 'Ambiguous move', 'Internal server error')
# - exit: true if the client should exit
# On 400 errors for 'move' responses, the server may also provide a 'suggestion' field with a list of possible moves.
#
# The engine will also log to the console and to EnPassant.log.

import asyncio
import json
import logging

# TODO: switch from websockets to zmq
import websockets

from config import (DEFAULT_ENGINE_OPTIONS, ENGINE_EXECUTABLE, ENGINE_PORT,
                    ENGINE_PW, ENGINE_USER)
from game_session import GameSession

logger = logging.getLogger(__name__)

class EngineSession(GameSession):
    '''
    Extends GameSession to manage an engine process for each session and to provide
    a method to get the best move and principal variations. The underlying GameSession
    should have an identical state to the client's game state at all times, or as much
    as possible in this asynchronous environment, i.e. if a new move is received before
    the engine has finished calculating the previous move, the new move should be applied
    to the GameSession and the engine should be told to stop calculating the previous move.
    This should be initialized after a client has requested a new game or to resume a game.
    '''
    def __init__(self, fen=None, moves=[], game_options={}, engine_options=DEFAULT_ENGINE_OPTIONS):
        super().__init__(fen, moves, game_options)


async def server(ws):
    while True:
        msg_str = await ws.recv()
        logger.debug(f'Received message from client: {msg_str}')
        msg = json.loads(msg_str)
        if msg.get('request') == 'exit':
            logger.info('Client requested exit')
            await ws.close()
            return

async def main():
    logger.info(f'Starting websocket server on port {ENGINE_PORT}')
    async with websockets.serve(server, '', ENGINE_PORT, create_protocol=websockets.basic_auth_protocol_factory(credentials=(ENGINE_USER, ENGINE_PW))):
        await asyncio.Future() # run forever
