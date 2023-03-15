# Implements admin-only slash commands.

import json
import logging
from pprint import pformat
from typing import Dict

import interactions

from command_defs import commands
from config import HOME_GUILD_ID

logger = logging.getLogger(__name__)

def admin_channel_only(func):
    '''Decorator to check if a command is used in the admin channel'''
    async def wrapper(ctx: interactions.CommandContext):
        # Check if the command was used in the admin channel
        if ctx.channel_id == int(commands['admin_commands']['CHANNEL_ID']):
            # If so, call the function
            await func(ctx)
        else:
            # If not, send an error message
            await ctx.send(content='Sorry, this command can only be used in the admin channel!')
    # Set the wrapper function's name to the name of the function it wraps
    wrapper.__name__ = func.__name__
    logger.debug(f'Created admin_channel_only decorator for {func.__name__}')
    return wrapper

# Defined here so it can be imported by other modules
async def refresh_emoji_names(client: interactions.Client) -> Dict[str, str]:
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
    with open('emoji_map.json', 'w') as f:
        json.dump(emoji_map, f, indent=4)
        logger.debug('Saved emoji map to file')
    return emoji_map

def register_admin_commands(client: interactions.Client):

    @client.command(
        name=commands['admin_commands']['refresh_emoji_cache']['name'],
        description=commands['admin_commands']['refresh_emoji_cache']['description'],
        scope=commands['admin_commands']['GUILD_ID']
    )
    @admin_channel_only
    async def _refresh_emoji_names(client: interactions.Client):
        return refresh_emoji_names(client)
    
    @client.command(
        name='eval',
        description='Just eval. Please use responsibly, and note that the bot is not running as admin.',
        scope=commands['admin_commands']['GUILD_ID'],
        options=[
            interactions.Option(
                name='code',
                description='The code to evaluate',
                type=interactions.OptionType.STRING,
                required=True
            )
        ]
    )
    @admin_channel_only
    async def _eval(ctx: interactions.CommandContext, code: str) -> None:
        '''Evaluate the given code'''
        result = pformat(eval(code))
        logger.warning(f'Evaluated code: {code} -> {result}')
        await ctx.send(content=f'```{result}```')

