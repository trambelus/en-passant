import asyncio
import json
import logging
from typing import Any, Literal

import interactions
import websockets
from attrs import define
from chess import (BLACK, WHITE, AmbiguousMoveError, Board, IllegalMoveError,
                   InvalidMoveError)
from interactions import Snowflake

from config import (DEFAULT_GAME_OPTIONS, ENGINE_HOST, ENGINE_PORT, ENGINE_PW,
                    ENGINE_USER)
from game import GameSession, correct_bad_move, disambiguate_move

from .client_options import ClientOptions
from .client_utils import board_to_emoji
from .strings import (checkmate_1p, checkmate_2p, checkmate_2p_upset, draw_1p,
                      draw_2p, interloper, resign_2p, stalemate_1p,
                      stalemate_2p)

    # checkmate_string, stalemate_string, draw_string, resign_string, interloper_string, \
    # illegal_move_string, invalid_move_string, ambiguous_move_string, check_string, move_string, \
    # game_over_string, game_start_string, game_cancel_string, game_cancelled_string, game_cancel_fail_string, \
    # game_cancel_fail_not_found_string, game_cancel_fail_not_your_turn_string, game_cancel_fail_not_your_game_string, \
    # game_cancel_fail_not_started_string, game_cancel_fail_not_in_progress_string, game_cancel_fail_not_finished_string, \
    # ai_game_start_string, ai_game_cancel_string, ai_game_cancelled_string, ai_game_cancel_fail_string, \
    # ai_game_cancel_fail_not_found_string, ai_game_cancel_fail_not_your_turn_string, ai_game_cancel_fail_not_your_game_string, \
# Those were all generated by Copilot and might not be implemented, but I'm leaving them there for inspiration.
    

logger = logging.getLogger(__name__)


def moves_to_board(moves: str) -> Board:
    '''Given a string of moves, return a chess.Board'''
    # Create a new GameSession (useful for parsing moves)
    game_session = GameSession()
    for move in moves.split(' '):
        if not game_session.push_move_str(move):
            raise ValueError('Invalid move')
    return game_session.board

def moves_to_fen(moves: str) -> str:
    '''Given a string of moves, return a FEN string'''
    # Get the board from the moves
    board = moves_to_board(moves)
    # Return the FEN string
    return board.fen()

# TODO: maybe subclass this into two classes (player-vs-engine games and player-vs-player games)
class ClientGameSession(GameSession):
    '''
    A GameSession that can be used to connect to a chess engine, or handle a game between two human players.
    Includes a websocket connection to the engine, and a session ID for the engine to identify the game.
    game_options includes the options that are relevant to both the client and the engine; see the GameSession class for details.
    client_options includes only the options that are relevant to the client; see the ClientOptions class for details.
    '''
    def __init__(self, client_options: ClientOptions, fen: str = None, moves: list[str] = [], game_options: dict[str, Any] = DEFAULT_GAME_OPTIONS, session_id: Snowflake = None):
        '''
        Create a new ClientGameSession.
        :param ClientOptions client_options: The options that are relevant to the client.
        :param str fen: The FEN string to start the game from.
        :param list[str] moves: The moves to make in the game. Overrides the FEN string if both are present.
        :param dict[str, Any] game_options: The options that are relevant to both the client and the engine.
        :param Snowflake session_id: The session ID to use for the game. Should match the thread ID.
        '''
        # session_id is converted to string because Snowflake is not JSON serializable.
        # Also GameSession really shouldn't have to deal with Snowflake objects; those are Discord-specific.
        # TODO: figure out what happens if the session ID is not provided.
        super().__init__(fen=fen, moves=moves, game_options=game_options, session_id=str(session_id))
        self.client_options: ClientOptions = client_options
        self.flavor_state = {
            # Various state information for providing more fun flavor text
            'spectators': [], # Discord IDs of spectators
            'interlopers': {}, # Discord IDs of players who have attempted to join the game but are not allowed to, mapped to flavor text generators (TODO)
        }
        # If the game is vs the engine, connect to the engine
        if self.client_options.players == 1:
            # TODO: sort out once and for all whether session_id comes from the engine or the client.
            # Also stop coding this late at night.
            # For now I'm going to assume that the client generates the session ID and sends it to the engine.
            # The engine will then send the session ID back to the client.
            # The client will then send the session ID to the engine when it makes a move.
            # This is ridiculous. I'm going to bed.
            self.ws = None
            asyncio.run(self.connect()) # Is this the right way to do this?
        # Offer state can be a single Offer, since only one offer can be active at a time.
    
    def __str__(self):
        '''Return a string representation of the game.'''
        # Get the author's id
        author_name = self.client_options.author_nick
        # Get the opponent's id
        opponent_name = self.client_options.opponent_nick
        # Get the game's name
        name = self.client_options.name
        # Get the list of moves
        moves = self.moves
        # Get the client options
        client_options = str(self.client_options)
        return f'GameSession({author_name}, {opponent_name}, {name}, {moves}, {client_options})'
    
    @property
    def current_player_id(self) -> Snowflake:
        '''The ID of the player whose turn it is.'''
        return self.client_options.get_id(self.board.turn)

    @property
    def other_player_id(self) -> Snowflake:
        '''The ID of the player whose turn it is not.'''
        return self.client_options.get_id(not self.board.turn)

    @property
    def current_player_name(self) -> str:
        '''The name of the player whose turn it is.'''
        return self.client_options.get_nick(self.board.turn)
    
    @property
    def other_player_name(self) -> str:
        '''The name of the player whose turn it is not.'''
        return self.client_options.get_nick(not self.board.turn)
    
    @property
    def current_player_mention(self) -> str:
        '''The mention (nickname or ping, depending on options) of the player whose turn it is.'''
        return self.client_options.get_ping_or_nick(self.board.turn)
    
    @property
    def other_player_mention(self) -> str:
        '''The mention (nickname or ping, depending on options) of the player whose turn it is not.'''
        return self.client_options.get_ping_or_nick(not self.board.turn)
    
    def new_game(self):
        '''
        Start a new game.
        '''
        author_nick = self.client_options.author.nick
        opponent_nick = self.client_options.opponent.nick
        author_color = 'white' if self.client_options.author.color else 'black'
        ret_str = f'New game started between {author_nick} ({author_color}) and {opponent_nick}.\n'
        ret_str += self.get_last_move_response()
        return ret_str

    def make_move(self, move_str: str, mover: interactions.Member) -> str:
        '''
        After running various checks, make a move.
        Verify the author of the move, send the move to the engine, display the move on the board, ping the opponent, and update the clock.
        It's the caller's responsibility to verify that this GameSession corresponds to the channel in which the move was made.
        '''

        # TODO: replace all these with flavor text in flavor_strings.py
        if mover is None:
            return 'Something went wrong on the backend. I don\'t even know who you are.'
        
        if mover.user.id != self.client_options.black_player.id and mover.user.id != self.client_options.white_player.id:
            return f'You are not a player in this game, {mover.nick or mover.user.username}.'
        
        elif mover.user.id != self.client_options.white_player.id and self.turn == WHITE:
            return f'It is not your turn, {self.client_options.black_player.nick}!'
        
        elif mover.user.id != self.client_options.black_player.id and self.turn == BLACK:
            return f'It is not your turn, {self.client_options.white_player.nick}!'
        
        # Check the move for validity
        try:
            move = self.parse_move(move_str)

        except (InvalidMoveError, IllegalMoveError):
            suggestions = correct_bad_move(move_str, self.board)
            if suggestions and len(suggestions) > 1:
                return f'Invalid move \'**{move_str}**\'! Did you mean one of these? [**{"**, **".join(suggestions)}**]'
            elif suggestions and len(suggestions) == 1:
                return f'Invalid move \'**{move_str}**\'! Did you mean **{suggestions[0]}**?'
            else:
                return f'Invalid move \'**{move_str}**\'! Did you mean to type `/resign`?'
            
        except AmbiguousMoveError:
            suggestions = disambiguate_move(move_str, self.board)
            if suggestions and len(suggestions) > 2:
                # e.g. "Did you mean x, y, or z?"
                return f'Ambiguous move \'**{move_str}**\'! Did you mean **{"**, **".join(suggestions[:-1])}**, or **{suggestions[-1]}**?'
            elif suggestions and len(suggestions) == 2:
                # e.g. "Did you mean x or y?"
                return f'Ambiguous move \'**{move_str}**\'! Did you mean **{suggestions[0]}** or **{suggestions[1]}**?'
            elif suggestions and len(suggestions) == 1:
                # This should never happen, but just in case...
                return f'Ambiguous move \'**{move_str}**\'! Did you mean **{suggestions[0]}**?'
            logger.error(f'No suggestions for ambiguous move {move_str}!')
            return f'Ambiguous move \'**{move_str}**\'! I don\'t know what you mean.'
        
        # If the move is valid, make it
        self.push_move(move)
        
        # If the game is vs the engine, send the move to the engine
        if self.client_options.players == 1:
            self.send_move(move)

        # Get additional information about the move
        check_warning_str = self.check_warning(move_str)

        # Return a string showing the moves, the board, and the move info
        ret_str = self.get_last_move_response(check_warning_result=check_warning_str)
        return ret_str
    
    def get_last_move_response(self, check_warning_result: str = None) -> str:
        '''
        Get the response to the last move on the board stack.
        This includes the moves list, the board, and (maybe) a note about check or checkmate.
        '''

        ret_str = ''

        # Convert the board to emoji, sending the list of SAN-formatted moves if the notation is SAN
        if self.client_options.notation == 'san':
            ret_str += board_to_emoji(self.board, self.moves)
        elif self.client_options.notation == 'uci':
            ret_str += board_to_emoji(self.board)

        # Add any game state info from the last move
        if check_warning_result:
            ret_str += f'\n**{check_warning_result}**'

        if self.is_game_over:
            if self.is_checkmate:
                winner = self.other_player_mention # The player who just moved is the winner
                loser = self.current_player_mention # The player whose turn it is now is the loser
                ret_str += f'\n{next(checkmate_2p if self.client_options.players == 2 else checkmate_1p).format(winner=winner, loser=loser)}'
            elif self.is_stalemate:
                ret_str += f'\n{next(stalemate_2p if self.client_options.players == 2 else stalemate_1p)}'
            # No need to do anything else; caller will check if the game is over as well

        else: # If it's not game over, maybe ping the next player
            # TODO: add flavor text here too
            ping_str = self.client_options.get_ping_str(self.turn)
            if ping_str:
                ret_str += f'\n{ping_str}, it\'s your turn!'

        return ret_str
    
    def process_draw_offer(self, offer_author: interactions.Member) -> str:
        '''
        Process a draw offer from a player.
        '''
        # Check if another offer is already pending
        if self.current_offer:
            # Is it a draw offer, and is it from the other player?
            if self.current_offer.offer_type == 'draw' and offer_author.user.id != self.current_offer.author.id:
                # If so, accept the draw
                self.current_offer.status = 'accepted'
                self.status.outcome = 'draw'
                return f'**{offer_author.nick or offer_author.user.username}** accepted the draw offer from **{self.current_offer.offer_author.nick or self.current_offer.offer_author.user.username}**!'
            

    def send_move(self, move_str: str) -> None:
        '''
        Send a move to the engine.
        '''
        raise NotImplementedError
        self.ws.send(json.dumps({'request': 'move', 'session_id': self.session_id, 'move': move_str}))    
    
    async def connect(self):
        connection_string = f'wss://{ENGINE_USER}:{ENGINE_PW}@{ENGINE_HOST}:{ENGINE_PORT}'
        self.ws = await websockets.connect(connection_string)
        await self.ws.send(json.dumps({'request': 'new', 'game_options': self.game_options}))
        response = json.loads(await self.ws.recv())
        if response['code'] != 200:
            logger.error(f'Failed to connect to engine: {response["message"]}')
        else:
            self.session_id = response['session_id']
            self.connected = True

    async def disconnect(self):
        await self.ws.send(json.dumps({'request': 'exit'}))
        await self.ws.close()
        self.connected = False
    
    def to_dict(self) -> dict[str, Any]:
        '''
        Convert the game to a serializable object.
        '''
        ret = super().to_dict()
        ret['client_options'] = self.client_options.to_dict()
        return ret

    @classmethod
    def from_dict(cls, json_dict: dict[str, str]) -> 'ClientGameSession':
        '''Load a game from a serialized object'''
        json_dict['client_options'] = ClientOptions.from_dict(json_dict['client_options'])
        return cls(**json_dict)
    