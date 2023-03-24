import json
import logging
from functools import wraps
from pprint import pformat
from datetime import datetime, timedelta

import interactions

from config import EMOJI_CACHE_FILE, HOME_GUILD_ID

from .command_definitions import commands

logger = logging.getLogger(__name__)

# Defined here so it can be imported by other modules
async def refresh_emoji_names(client: interactions.Client) -> dict[str, str]:
    '''Get a list of all the emoji names from the server and use them to populate emoji_map'''
    # Get the list of emoji from the server
    emoji_map = {}
    try:
        emoji_list = await client._http.get_all_emoji(int(HOME_GUILD_ID))
    except interactions.HTTPException as e:
        logger.error(f'Failed to get emoji list from Discord API: {e} {e.response}')
        return False
    # Iterate over the emoji
    for emoji in emoji_list:
        # Get the emoji name
        emoji_name = emoji['name']
        # Add the emoji name to the map
        emoji_map[emoji_name] = f'<:{emoji_name}:{emoji["id"]}>'
        logger.debug(f'Added emoji {emoji_name} to map with id {emoji["id"]}')
    # Save the emoji map to the JSON file
    with open(EMOJI_CACHE_FILE, 'w') as f:
        json.dump(emoji_map, f, indent=4)
        logger.debug('Saved emoji map to file')
    return emoji_map

def admin_channel_only(func):
    '''Decorator to check if a command is used in the admin channel'''
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get the context from the arguments
        ctx = args[0]
        # Check for type safety, and if it's not there, log an error
        if not isinstance(ctx, interactions.CommandContext):
            logger.error(f'admin_channel_only decorator called with invalid context: {pformat(ctx)}')
            return
        # Check if the command was used in the admin channel
        if ctx.channel_id == int(commands['admin_commands']['CHANNEL_ID']):
            # If so, call the function
            return await func(*args, **kwargs)
        else:
            # If not, send an error message
            await ctx.send(content='Sorry, this command can only be used in the admin channel!', ephemeral=True)

    logger.debug(f'Created admin_channel_only decorator for {func.__name__}')
    return wrapper

def cooldown(seconds: int):
    '''Decorator to add a cooldown to a command, in seconds.
    The cooldown is per user and per channel, and if set to 0,
    this decorator will only prevent the command from being called more than once at a time
    by the same user in the same channel.'''
    def decorator(func):
        # Enforce cooldowns with a dict keyed by user ID and channel ID, with the value being the time the cooldown expires
        cooldowns: dict[tuple[str, str], datetime] = {}
        # Use a second dict to ensure that the wrapped function isn't called twice at the same time
        cooldown_locks: dict[tuple[str, str], bool] = {}
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the context from the arguments
            ctx = args[0]
            # Check for type safety, and if it's not there, log an error
            if not isinstance(ctx, interactions.CommandContext):
                logger.error(f'cooldown decorator called with invalid context: {pformat(ctx)}')
                return
            # Get the user ID and channel ID
            user_id = str(ctx.author.id)
            channel_id = str(ctx.channel_id)
            # Check if the user is on cooldown
            if cooldowns.get((user_id, channel_id), datetime.now()) > datetime.now():
                # If so, send an error message
                await ctx.send(content=f'Sorry, this command is on cooldown for {cooldowns[(user_id, channel_id)] - datetime.now()} more seconds!', ephemeral=True)
                return
            # Check if the user is already locked
            if cooldown_locks.get((user_id, channel_id), False):
                # If so, send an error message
                await ctx.send(content='Sorry, this command is already running!', ephemeral=True)
                return
            # If not, lock the user
            cooldown_locks[(user_id, channel_id)] = True
            # Call the function
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # Unlock the user
                cooldown_locks[(user_id, channel_id)] = False
                # Set the cooldown
                cooldowns[(user_id, channel_id)] = datetime.now() + timedelta(seconds=seconds)

        logger.debug(f'Created cooldown decorator for {func.__name__}, with cooldown of {seconds} seconds')
        return wrapper
    return decorator