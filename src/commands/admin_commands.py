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

    admin_commands = commands['admin_commands']

    @client.command(**admin_commands['refresh_emoji_names'])
    @admin_channel_only
    async def _refresh_emoji_names(client: interactions.Client):
        return refresh_emoji_names(client)
    
    @client.command(**admin_commands['eval'])
    @autodefer()
    @admin_channel_only
    async def __eval(ctx: interactions.CommandContext, expression: str) -> None:
        # Disabled for now. This is a security risk, and I don't want to deal with it. Plus, it's not like I use it anyway.
        # return await _eval(ctx, expression)
        await ctx.send(content='**WARNING**: You do not have permission to use this command. This action has been logged.')
        # Does not log anything, of course, but it's a sort of fun scare tactic.
    
    async def _eval(ctx: interactions.CommandContext, expression: str) -> None:
        '''Evaluate the given code'''
        try:
            result = pformat(await eval(expression))
            logger.warning(f'Evaluated code: {expression} -> {result}')
            await ctx.send(content=f'```{result}```')
        except Exception as e:
            logger.error(f'Exception while evaluating code: {e}')
            logger.exception(e)
            await ctx.send(content=f'```Exception: {e}```')
    
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
