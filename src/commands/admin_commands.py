# Implements admin-only slash commands.

import logging
from asyncio import sleep
from pprint import pformat

import interactions
from interactions.api.models import Channel
from interactions.utils import autodefer, get

from config import EMOJI_CACHE_FILE, HOME_GUILD_ID

from .command_definitions import commands
from .command_utils import refresh_emoji_names, admin_channel_only

logger = logging.getLogger(__name__)

def register_admin_commands(client: interactions.Client):

    logger.info('Registering admin commands')

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
        description='Just eval—please use responsibly, and note that the bot is not running as admin.',
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
    async def __eval(ctx: interactions.CommandContext, code: str) -> None:
        return await _eval(ctx, code)
    
    @admin_channel_only
    async def _eval(ctx: interactions.CommandContext, code: str) -> None:
        '''Evaluate the given code'''
        result = pformat(eval(code))
        logger.warning(f'Evaluated code: {code} -> {result}')
        await ctx.send(content=f'```{result}```')
    
    @client.command(
        name='test-contextless',
        description='Attempt to send a message without a context after a delay of 5 seconds',
        scope=commands['admin_commands']['GUILD_ID']
    )
    @admin_channel_only
    async def test_contextless(ctx: interactions.CommandContext) -> None:
        # Send an acknowledgement message to the context so it doesn't show as failed
        await ctx.send(content='Sending message in 5 seconds...')
        # Get the channel from the context, and then get a new channel object from the ID with no reference to the context
        channel_id: int = int(ctx.channel.id)
        channel: Channel = await get(client, Channel, object_id=channel_id)
        # Wait 5 seconds
        await sleep(5)
        # Send a message in the channel
        await channel.send(content='This is a test message sent without a context!')
    
    @client.command(
        name='test-autodefer',
        description='Attempt to send an auto-deferred message after a delay of 5 seconds',
        scope=commands['admin_commands']['GUILD_ID']
    )
    @autodefer()
    @admin_channel_only
    async def test_autodefer(ctx: interactions.CommandContext) -> None:
        # Wait 5 seconds
        await sleep(5)
        # Send a message in the channel
        await ctx.send(content='This is a test message sent with autodefer!')
