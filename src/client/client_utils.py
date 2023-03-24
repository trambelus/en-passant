# Provides a set of utility functions for the client.

import re
import datetime
import inspect
from functools import wraps
import logging

from interactions import Snowflake, Client
from interactions.api.models.channel import Channel
from interactions.api.models.message import Message, MessageType
from interactions.api.models.user import User
from interactions.utils.get import get
from chess import Piece, Board

from config import BOT_ID

logger = logging.getLogger(__name__)

# Map pieces to emoji names
pieces_map = {
    'P': 'pw',
    'R': 'rw',
    'N': 'nw',
    'B': 'bw',
    'Q': 'qw',
    'K': 'kw',
    'p': 'pb',
    'r': 'rb',
    'n': 'nb',
    'b': 'bb',
    'q': 'qb',
    'k': 'kb',
    '.': '__'
}

# Map emoji names to emoji references, e.g. 'pw' -> '<:pw:1084899251366133802>'
# Must be initialized after the bot is logged in, since the emoji IDs change whenever the server's emojis are updated
# TODO: just use a single map for both pieces_map and emoji_map, this is silly
emoji_map = {}

def populate_emoji_map(new_map: dict[str, str]):
    '''Populate emoji_map with the current emoji references.'''
    for piece, emoji in new_map.items():
        emoji_map[piece] = emoji
    logger.debug(f'Populated emoji_map in client_utils.py: {emoji_map}')

def fen_to_emoji(fen: str) -> str:
    '''Given a FEN string, return a string that can be used in a Discord message'''
    board = Board(fen)
    return board_to_emoji(board)

def board_to_emoji(board: Board, moves_list: list[str] = None) -> str:
    '''Given a board from chess.py, return a string that can be used in a Discord message,
    e.g. given a board with the starting position, return:
    [list of moves, blank in this case]
    :rbl::nbd::bbl::qbd::kbl::bbd::nbl::rbd: `8`
    :pbd::pbl::pbd::pbl::pbd::pbl::pbd::pbl: `7`
    :__l::__d::__l::__d::__l::__d::__l::__d: `6`
    :__d::__l::__d::__l::__d::__l::__d::__l: `5`
    :__l::__d::__l::__d::__l::__d::__l::__d: `4`
    :__d::__l::__d::__l::__d::__l::__d::__l: `3`
    :pwl::pwd::pwl::pwd::pwl::pwd::pwl::pwd: `2`
    :rwd::nwl::bwd::qwl::kwd::bwl::nwd::rwl: `1`
    ` a  b  c  d  e  f  g  h  `
    Not quite like that, each emoji will be a fully-qualified reference, e.g. <:pwl:1084899251366133802>,
    but that would be too long for this comment.
    '''
    # If emoji_map is empty, error out
    if len(emoji_map) == 0:
        raise ValueError('emoji_map is empty, please call populate_emoji_map(new_map) first')
    # If moves_list is None, try to get the moves from the board
    if moves_list is None:
        moves_list = [move.uci() for move in board.move_stack]
    # Get the last move, if any
    last_move = board.peek() if len(board.move_stack) > 0 else None
    # Get a string representation of the moves list
    if len(moves_list) == 0:
        moves_str = ''
    else:
        # Add move numbers every other move, and with the last move wrapped with '**'
        moves_str = ''.join([(f'  {i // 2 + 1}. ' if i % 2 == 0 else ' ') + f'{"**" if i == len(moves_list) - 1 else ""}{move}' for i, move in enumerate(moves_list)]) + '**'
    # Get a representation of the board as a 2D array
    board_str = str(board)
    board_arr = [rank.split(' ') for rank in board_str.split('\n')]
    # Isolate the relevant squares from the last move, if any, for highlighting
    (fr, ff, tr, tf) = (7 - last_move.from_square // 8, last_move.from_square % 8, 7 - last_move.to_square // 8, last_move.to_square % 8) if last_move else (None, None, None, None)
    # Convert to a 2D array of emoji names
    board_arr = [[f'{pieces_map[board_arr[r][f]]}{"h" if ((r == fr and f == ff) or (r == tr and f == tf)) else ("l" if (r + f) % 2 == 0 else "d")}' for f in range(len(board_arr[r]))] for r in range(len(board_arr))]
    # Convert the board array into a list of strings, each string representing a rank
    ranks_arr = [' ' + ''.join([emoji_map[p] for p in board_arr[r]]) + f' `{8-r}`' for r in range(len(board_arr))]
    # Add the move list as an initial string
    ranks_arr.insert(0, moves_str)
    # Add the file labels as a final string
    ranks_arr.append('` a  b  c  d  e  f  g  h  `')
    # Join the lines into a single string and return it
    return '\n'.join(ranks_arr)

def emoji_to_fen(emoji: str) -> str:
    '''Given a string that can be used in a Discord message, return a FEN string'''
    # Get the board from the emoji
    board = emoji_to_board(emoji)
    # Return the FEN string
    return board.fen()

def emoji_to_board(message_str: str) -> Board:
    '''Given a string that can be used in a Discord message, return a chess.Board'''
    # Create a new empty board
    board = Board(fen=None)
    # Discard the first line (the move list) if it exists (starts with '1. ')
    if message_str.split('\n')[0].startswith('1. '):
        message_str = '\n'.join(message_str.split('\n')[1:])
    # Discard the last line (the file labels) if it exists (starts with '` a ')
    if message_str.split('\n')[-1].startswith('` a ') or message_str.split('\n')[-1].strip().startswith('a'):
        message_str = '\n'.join(message_str.split('\n')[:-1])
    # Discard the file labels at the end of each line if they exist
    message_str = '\n'.join([line.strip().split(' ')[0] for line in message_str.split('\n')])
    # Get the ranks from the emoji
    ranks = message_str.split('\n')
    if len(ranks) != 8:
        print(f'Invalid number of ranks: {len(ranks)}')
        print(f'Ranks: {ranks}')
        raise ValueError('Invalid number of ranks')
    # Iterate over the ranks
    for r in range(len(ranks)):
        # Get the squares from the rank
        squares = ranks[r].split('::')
        # Iterate over the squares
        for f in range(len(squares)):
            # Get the piece from the square
            emoji = squares[f].replace(':', '')
            piece = emoji[0].upper() if emoji[1] == 'w' else emoji[0]
            # If the square is not empty, add the piece to the board
            if piece != '_':
                board.set_piece_at((7 - r) * 8 + f, Piece.from_symbol(piece))
    # Return the board
    return board


def to_discord_snowflake(id: str | int) -> Snowflake:
    '''
    Convert a string or an int to a Snowflake.
    Must be a valid Discord snowflake, or else a TypeError or ValueError will be raised.
    '''
    # Define a regular expression for the snowflake id format.
    # Catches ids with e.g. invalid characters, too many digits, or too few digits.
    snowflake_pattern = re.compile(r"^\d{18}$")

    # Define constant for Discord's epoch.
    # Discord uses a custom epoch that makes it easy to distinguish between Discord snowflakes and others (e.g. Twitter's).
    DISCORD_EPOCH = 1420070400000 # 2015-01-01 00:00:00

    # Check if it's already a Snowflake. If it is, just return it.
    if isinstance(id, Snowflake):
        return id
    
    # Ensure that it's a string or int.
    if isinstance(id, int):
        id = str(id)
    elif not isinstance(id, str):
        raise TypeError(f"Could not validate snowflake: {id} is not a string or an int")

    # Check if it matches the snowflake regex.
    if not snowflake_pattern.match(id):
        raise ValueError(f"Could not validate snowflake: {id} is not a valid snowflake id")
    
    # Convert it to int for further validation.
    # Further documentation on these checks can be found at https://discord.com/developers/docs/reference#snowflakes
    id = int(id)

    # Check if it fits in a signed bigint.
    if not (-2**63 <= id < 2**63):
        raise ValueError(f"Could not validate snowflake: {id} is out of range for a signed bigint")
    
    # Extract the timestamp portion of the id by shifting left by 22 bits
    timestamp = (id >> 22) + DISCORD_EPOCH

    # Convert the timestamp to a datetime object
    timestamp = datetime.datetime.fromtimestamp(timestamp / 1000)

    # Check if it is after Discord's epoch
    if timestamp < datetime.datetime(2015, 1, 1):
        raise ValueError(f"Snowflake {id} has an invalid timestamp before Discord's epoch")
    
    # Return the Snowflake object
    return Snowflake(id)

def validate_discord_snowflake(func):
    '''
    Decorator to validate a Discord snowflake ID as the first argument of a function.
    If the ID is already a Snowflake, it will be passed through; if not, it will be converted to a Snowflake.
    If the ID is not a valid Discord snowflake, a TypeError or ValueError will be raised.
    Works for both free functions and bound methods.
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        # default for free functions and static methods
        id_index = 0
        # check if the function is a method.
        # since this is a decorator, the wrapper itself will become a method in place of the original function, so we need to check the wrapper.
        if hasattr(args[0], '__dict__') and inspect.ismethod(getattr(args[0], func.__name__, None)):
            # check second argument
            id_index = 1
        else:
            # check first argument
            id_index = 0

        # replace the id with a Snowflake, if it's not already one
        if not isinstance(args[id_index], Snowflake):
            id = to_discord_snowflake(args[id_index])
            args = list(args)
            args[id_index] = id

        # call the original function
        return func(*args, **kwargs)

    # return the wrapper function
    return wrapper

def get_moves(msg_str: str) -> str | None:
    '''
    Get the moves from a message.
    '''
    # Define a regex that matches anything that looks vaguely like a list of moves
    # More robust move parsing is done elsewhere
    # TODO: define all the regexes in one place, to make it easier to update them for new features (e.g. variants)
    chesslike_regex = r'(?:\d+\. *(?:[KQRBNOa-hx][\w=+#]+ *(?:[0\-1/]*)?){1,2} *){1,}'
    # Isolate the string that contains the moves
    try:
        moves_str = re.search(chesslike_regex, msg_str)[0]
    except TypeError:
        return None
    return moves_str

def contains_moves(msg: Message) -> bool:
    '''
    Check if a message contains a list of moves.
    '''
    # Ignore messages not sent by the bot
    if msg.author.id != BOT_ID:
        return False
    # Return true if the message contains a list of moves
    return get_moves(msg.content) is not None

async def get_last_moves(channel: Channel) -> list[str]:
    '''
    Get the last message in a channel that corresponds to a move in a chess game (i.e. a message that contains a list of moves).
    '''
    msg = await anext(channel.history(start_at=channel.last_message_id, maximum=100, reverse=True, check=contains_moves), None)
    if msg is None:
        return None
    # Get the moves from the message
    moves_str = get_moves(msg.content)
    # Remove the move numbers and split the string into a list of moves
    moves_list = re.sub(r' *\d+\. *', ' ', moves_str).strip().split(' ')
    # Remove empty strings
    ret = [move for move in moves_list if move]
    logger.debug(f'get_last_moves: Found moves: {ret}')
    return ret

async def cleanup(client: Client, msg_id: int | str | Snowflake, channel_id: Snowflake) -> bool:
    '''
    Clean up after a failed execution of some sort.
    This includes deleting the "new game" message (which should match the ID), 
    deleting the thread (if it exists), and sending an ephemeral message to the user (which the caller handles).
    '''
    # Get the channel
    channel: Channel = await get(client=client, obj=Channel, object_id=channel_id)
    # Get the message
    target_msg: Message = await get(client=client, obj=Message, object_id=msg_id, channel_id=channel_id)
    # There seems to be some inconsistency in whether the THREAD_CREATED message is above or below the new game message,
    # so we need to check both.
    related_msg: Message = None
    try:
        # Get the message below the target message, filtering by the bot's ID
        # Should be able to use msg.author.id == BOT_ID, but I don't see __eq__ defined for Snowflake despite the docs saying it is, so we'll just compare the strings
        related_msg: Message = await anext(channel.history(start_at=msg_id, maximum=10, reverse=True, check=lambda msg: str(msg.author.id) == BOT_ID))
    except StopAsyncIteration:
        logger.debug("No message below the new game message")
        pass
    try:
        # Get the message above the target message, filtering by the bot's ID, if we haven't found one yet
        if related_msg is None:
            related_msg: Message = await anext(channel.history(start_at=msg_id, maximum=10, reverse=False, check=lambda msg: str(msg.author.id) == BOT_ID))
    except StopAsyncIteration:
        logger.debug("No message above the new game message (???)")
        pass
    try:
        for msg in (m for m in [target_msg, related_msg] if m is not None):
            if msg.type == MessageType.THREAD_CREATED:
                # Delete the thread
                thread: Channel = await get(client=client, obj=Channel, object_id=msg.thread.id)
                await thread.delete()
            # Delete the message
            await msg.delete()
        return True
    except Exception as e:
        logger.error(f"Failed to delete messages: {e}")
        logger.exception(e)
        return False
