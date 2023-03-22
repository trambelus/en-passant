# Common elements for client and server relating to game state

import logging
import re
import uuid
from typing import Any

import chess
import chess.variant

from config import DEFAULT_GAME_OPTIONS

logger = logging.getLogger(__name__)

def generate_session_id():
    return str(uuid.uuid4())[8] # doesn't need to be secure, just unique

class GameSession:
    '''
    Maintains game state and provides methods to interact with it.
    This is sort of an abstract class, meant to maintain a common state for both the client and server,
    and should be extended by each to provide __enter__ and __exit__ methods for cleanup.
    It's still possible to use this class directly, but it won't do anything useful.
    Game options are not specific to the client or engine, and may (TODO: eventually?) include:
    - variant: the variant to play, e.g. 'atomic', 'crazyhouse', 'horde', 'kingofthehill', 'racingkings', 'threecheck'
    - chess960_pos: the starting position for chess960, or -1 for standard chess
    - time_limit: the time limit for each player, in seconds
    - increment: the increment for the game, in seconds
    '''
    def __init__(self, fen: str = None, moves: list[str] = [], game_options: dict[str, Any] = DEFAULT_GAME_OPTIONS, session_id: str | None = None):
        '''
        Set board, fen, game options, variant, chess960 position, and moves.
        :param str fen: the FEN string to set the board to
        :param list[str] moves: a list of moves in SAN or UCI format to apply to the board on init. Overrides fen string if both are present.
        :param dict[str, Any] game_options: a dictionary of game options (e.g. variant)
        :param str session_id: the session ID to use for this game session. If not provided, a random UUID will be used.
        Note: The session ID should generally match the Discord channel ID for the game.
        In the client session subclass, this is a Snowflake, but it's a string here to avoid a dependency on the interactions library in the backend.
        Note: fen and moves are mutually exclusive. If both are provided, moves will be applied to the board.
        If you want to apply moves to a board with a non-standard starting position, you'll need to set the board to the starting position first with reset_board(fen),
        then apply the moves with apply_moves(moves).
        '''
        self.session_id: str = str(session_id) or generate_session_id()

        self.game_options: dict[str, Any] = game_options
        self.variant: str = game_options.get('variant', 'standard') # TODO: implement variants
        # Handle chess960 start position
        try:
            self.chess960_pos = int(game_options.get('chess960_pos', -1))
        except ValueError:
            logger.warn(f'Invalid chess960 starting position \'{game_options.get("chess960_pos")}\'; defaulting to standard chess')
            self.chess960_pos = -1

        # Attempt to apply moves, if any, and revert to starting position if any are invalid.
        # If this fails, attempt to set the board from the fen parameter instead.
        # If that fails, set the board to the starting position.

        self.moves: list[str] = [] # list of moves in SAN format, maintained throughout the game since the board doesn't store them.
                                   # Stored as SAN regardless of whether the client wants moves displayed in SAN or UCI,
                                   # since the board does store them in UCI format (sort of) via board.move_stack.
        self.reset_board()
        if not self.apply_moves(moves):
            logger.warn('Could not apply moves; reverting to starting position')
            self.reset_board(fen=fen)
            self.moves = []
    
    def apply_moves(self, moves: list[str]) -> bool:
        '''
        Applies a list of moves to the board. Returns True if all moves were applied successfully, False otherwise.
        '''
        for move_str in moves:
            try:
                if move_str in ['0-1', '1-0', '1/2-1/2']:
                    logger.info(f'Loaded board from moves with game over indicated: {move_str}')
                    break
                move = self.parse_move(move_str)
                self.moves.append(self.board.san(move))
                self.board.push(move)
            except (chess.InvalidMoveError, chess.AmbiguousMoveError, chess.IllegalMoveError):
                logger.warn(f'Could not parse move \'{move_str}\' in moves list!')
                return False
        return True

    def reset_board(self, fen: str | None = None) -> chess.Board:
        if fen is not None:
            try:
                self.board = chess.Board()
                self.fen = fen # Also sets the board to the FEN string (gotta remember it's a property)
                return self.board
            except ValueError:
                logger.warn(f'Invalid FEN string \'{fen}\'; defaulting to starting position')
        if self.chess960_pos >= 0:
            self.board = chess.Board.from_chess960_pos(self.chess960_pos)
        elif self.variant is not None and self.variant != 'standard':
            try:
                self.board = chess.variant.find_variant(self.variant)()
                # Set variant name to the actual name of the variant, in case it matched a variant alias
                self.variant = self.board.uci_variant
            except ValueError:
                logger.warn(f'Unknown variant \'{self.variant}\'; defaulting to standard chess')
                self.board = chess.Board()
                self.variant = 'standard'
        else:
            self.board = chess.Board()
        return self.board

    def parse_move(self, move_str: str) -> chess.Move:
        '''
        Attempts to interpret a move first as UCI, then as SAN.
        If the move is syntatically invalid in both formats, illegal on the current board, or
        ambiguous, as indicated by the exception, throws the exception.
        '''
        move_str = move_str.replace('%20', ' ').replace('х', 'x') # A relic of the old days, when the client would send moves as a URL parameter
        move = None
        try:
            move = chess.Move.from_uci(move_str)
            # If the move is syntactically valid UCI, but illegal on the current board, we have to check for that, since from_uci doesn't.
            if not self.board.is_legal(move):
                raise chess.IllegalMoveError
        except chess.InvalidMoveError:
            # It's not valid UCI, so try SAN
            try:
                move = self.board.parse_san(move_str)
            except chess.InvalidMoveError as e:
                logger.warn(f'Invalid move: \'{move_str}\'')
                raise e
            except chess.AmbiguousMoveError as e:
                logger.warn(f'Ambiguous move: \'{move_str}\'')
                raise e
            except Exception as e:
                # If it's not an InvalidMoveError or AmbiguousMoveError, it's probably an IllegalMoveError, so we'll just re-raise it for the block below.
                # And if it's something else, we'll just let it propagate up.
                raise e
        except chess.IllegalMoveError as e:
            logger.warn(f'Illegal move: \'{move_str}\'')
            raise e
        return move

    def push_move(self, move: chess.Move) -> None:
        '''
        Pushes a move to the board.
        Raises an exception if the move is illegal.
        Please don't ever call this with illegal moves. That's what parse_move is for.
        '''
        previous_moves_len = len(self.moves)
        if move is not None:
            # Both board.san and board.push raise IllegalMoveError, but board.san doesn't catch all of them.
            # So it might be unclear whether self.moves was updated or not when an exception is raised,
            # so we'll keep track of the previous length and revert to that if an exception is raised.
            # It's the caller's responsibility to ensure that the move is legal BEFORE calling this method.
            try:
                self.moves.append(self.board.san(move))
                self.board.push(move)
            except chess.IllegalMoveError as e:
                # I would mark this as critical, but it's recoverable, so I'll just mark it as an error.
                logger.error(f'Illegal move in push_move: \'{move}\'. This should not happen.')
                self.moves = self.moves[:previous_moves_len]
                raise e

    def check_warning(self, move_str: str) -> str | None:
        '''If the given move specifies check or checkmate, verify that it is correct.
        Also provide messages for when check or other non-game-ending states have occurred.'''
        if self.board.is_check() and not self.board.is_checkmate():
            if move_str.endswith('#'):
                return 'User called a checkmate, but this move results in check!'
            else:
                return 'Check!'
        if move_str.endswith('+') and not self.board.is_check():
            return 'User called a check, but this move does not result in check!'
        if move_str.endswith('#') and not self.board.is_checkmate():
            return 'User called a checkmate, but this move does not result in checkmate!'
        return None
    
    def to_dict(self) -> dict[str, Any]:
        '''Returns a serializable dict representation of this object.'''
        # It shouldn't be strictly necessary to include the fen parameter, since it's only used in initialization
        # if the moves list is empty, but it's included for completeness.
        ret = {
            'fen': self.fen,
            'moves': self.moves,
            'game_options': self.game_options,
            'session_id': self.session_id,
        }
        logger.debug(f'GameSession.to_dict: {ret}')
        return ret

    @staticmethod
    def from_dict(d: dict[str, Any]) -> 'GameSession':
        '''Returns a GameSession object from the given dict.'''
        return GameSession(**d)

    # Properties
    @property
    def turn(self) -> chess.Color:
        '''Returns the color of the player whose turn it is.'''
        return self.board.turn

    @property
    def last_move(self) -> str:
        '''Returns the last move in SAN.'''
        return self.moves[-1] if len(self.moves) > 0 else None

    @property
    def fen(self) -> str:
        '''Returns the FEN of the current board position.'''
        return self.board.fen()

    @fen.setter
    def fen(self, fen: str | None) -> None:
        '''Sets the board position to the given FEN, or to the starting position if None is given.'''
        if fen is None:
            self.reset_board()
        else:
            self.board.set_fen(fen)

    @property
    def san_moves(self) -> list[str]:
        '''Returns the list of moves in SAN.'''
        return self.moves
    
    @property
    def uci_moves(self) -> list[str]:
        '''Returns the list of moves in UCI.'''
        return [move.uci() for move in self.board.move_stack]
    
    @property
    def is_game_over(self):
        '''Returns True if the game is over, False otherwise.'''
        return self.board.is_game_over()
    
    @property
    def is_check(self) -> bool:
        '''Returns whether the current player is in check.'''
        return self.board.is_check()
    
    @property
    def is_checkmate(self) -> bool:
        '''Returns whether the current player is in checkmate.'''
        return self.board.is_checkmate()
    
    @property
    def is_stalemate(self) -> bool:
        '''Returns whether the current player is in stalemate.'''
        return self.board.is_stalemate()
    
    @property
    def is_insufficient_material(self) -> bool:
        '''Returns whether the current player is in stalemate due to insufficient material.'''
        return self.board.is_insufficient_material()
    
    @property
    def is_seventyfive_moves(self) -> bool:
        '''Returns whether the current player is in stalemate due to the 75-move rule.'''
        return self.board.is_seventyfive_moves()
    
    @property
    def is_fivefold_repetition(self) -> bool:
        '''Returns whether the current player is in stalemate due to the 5-fold repetition rule.
        This method might be slow, so it's recommended to use it only when necessary.'''
        return self.board.is_fivefold_repetition()
    
    @property
    def is_variant_end(self) -> bool:
        '''Returns whether the current game is over due to the end of the variant.'''
        return self.board.is_variant_end()
    
    @property
    def is_variant_win(self) -> bool:
        '''Returns whether the current player has won due to the end of the variant.'''
        return self.board.is_variant_win()
    
    @property
    def is_variant_loss(self) -> bool:
        '''Returns whether the current player has lost due to the end of the variant.'''
        return self.board.is_variant_loss()
    
    @property
    def is_variant_draw(self) -> bool:
        '''Returns whether the current player has drawn due to the end of the variant.'''
        return self.board.is_variant_draw()
    
    @property
    def is_irreversible(self) -> bool:
        '''Returns whether the current position is irreversible.'''
        return self.board.is_irreversible()
    
    @property
    def is_repetition(self) -> bool:
        '''Returns whether the current position is a repetition.'''
        return self.board.is_repetition()


# Non-class functions

def levenshtein(s1: str, s2: str) -> int:
    '''Returns the levenshtein distance between the two given strings.'''
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def correct_bad_move(move_str: str, board: chess.Board) -> list[str]:
    '''
    Returns a list of all legal moves resembling the given move, in SAN format.
    If the given move string is more than 2 characters long, only moves that are within 2 levenshtein distance of the given move will be returned.
    Otherwise, all legal moves that are within 1 levenshtein distance of the given move will be returned.
    '''
    matches = []
    for legal_move in board.legal_moves:
        if levenshtein(move_str, board.san(legal_move)) <= min(2, len(move_str) - 1):
            matches.append(board.san(legal_move))
    return sorted(matches)

def disambiguate_move(ambiguous_san: str, board: chess.Board) -> list[str]:
    '''Returns a list of all legal moves that match the given ambiguous move string, in SAN format.'''
    matches = []
    for move in board.legal_moves:
        legal_move_tokens = tokenize_move(board.san(move))
        ambiguous_move_tokens = tokenize_move(ambiguous_san)
        if legal_move_tokens['piece'] == ambiguous_move_tokens['piece'] and \
            legal_move_tokens['to_rank'] == ambiguous_move_tokens['to_rank'] and \
            legal_move_tokens['to_file'] == ambiguous_move_tokens['to_file']:
            # All the legal moves that match the given move are the same piece moving to the same square
            matches.append(board.san(move))
        
    return matches

def tokenize_move(move: str) -> dict[str, str]:
    '''
    Returns a dict representing the parsed elements of the given move, whether in UCI or SAN format, e.g.:
    "Nbxc3+" ->
    {
        'piece': 'N',
        'from_file': 'b',
        'from_rank': None,
        'capture': 'x',
        'to_file': 'c',
        'to_rank': '3',
        'promotion': None,
        'check': '+',
        'result': None
    }
    The 'result' field, when present, will be '1-0', '0-1', or '1/2-1/2'.
    For SAN moves, the 'from_rank' and 'from_file' fields will be None if they are not specified, and 'piece' will be 'P' if no piece is specified.
    For UCI moves, the 'from_rank' and 'from_file' fields are always specified, and 'piece' will be None.
    But this method won't freak out if you give it a move that combines elements of both formats, e.g. 'e2xd3', which is underspecified for a standard SAN move,
    overspecified for a pawn SAN move, and includes a capture, which is not allowed in UCI.
    '''
    ret = {}
    pattern = re.compile(r'^(?:(?:(?P<piece>[KQRBN])?(?P<from_file>[a-h])?(?P<from_rank>[1-8])?(?P<capture>x)?(?P<to_file>[a-h])(?P<to_rank>[1-8])(?P<promotion>([=\/]?[QRBNqrbn]))?|(?P<castle>O-O(?:-O)?))(?P<check>[+#])?|(?P<result>1-0|0-1|1\/2-1\/2))$')
    match = pattern.match(move)
    if match:
        ret = match.groupdict()
        # Normalize promotion syntax (uppercase, strip prefix)
        if ret.get('promotion'):
            ret['promotion'] = ret['promotion'][-1].upper()
        # No piece specified means pawn, unless from_rank and from_file are both specified and capture is not (then it's a UCI move, not SAN)
        if not ret.get('piece') and not (ret.get('from_rank') and ret.get('from_file') and not ret.get('capture')):
            ret['piece'] = 'P'  
    return ret
