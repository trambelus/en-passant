# Provides a set of utility functions for the client.

import re
import datetime
import inspect
from functools import wraps
import logging
from asyncio import sleep

from interactions import Snowflake, Client
from interactions.api.models.channel import Channel
from interactions.api.models.message import Message, MessageType
from interactions.api.models.user import User
from interactions.utils.get import get

from config import BOT_ID

logger = logging.getLogger(__name__)

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
