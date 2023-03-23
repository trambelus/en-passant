# Implements slash commands available to all users, not directly related to a game.

import logging
import interactions
from .command_definitions import commands
from .command_utils import cooldown
import time

logger = logging.getLogger(__name__)

def register_user_commands(client: interactions.Client):
    '''Implement and implicitly register user-related slash commands.'''

    logger.info("Registering user commands")

    user_commands = commands['user_commands']

    # Decorators take care of registering the commands with the interactions library.
    @client.command(**user_commands['help'])
    async def help(ctx: interactions.CommandContext, topic: str = None) -> None:
        '''Get help. If a topic is specified, get help on that topic.'''
        # TODO: move these help strings to client/strings.py
        # TODO: also update this so it's not just filler code
        if topic:
            if topic in user_commands:
                await ctx.send(content=user_commands[topic]['description'])
            else:
                await ctx.send(content=f'No help available for topic "{topic}".')
        else:
            await ctx.send(content='''En Passant Bot is a Discord bot that allows you to play chess with your friends. To get started, type `/new` to create a new game. You can also type `/help` to get help on a specific topic or command.''')
    
    @client.command(**user_commands['ping'])
    @cooldown(5)
    async def ping(ctx: interactions.CommandContext) -> None:
        '''Ping the bot.'''
        start_time: float = time.monotonic()
        # Send and edit a message to test latency
        msg = await ctx.send(content='Pinging...')
        end_time: float = time.monotonic()
        await msg.edit(content=f'Pong! Latency: {round((end_time - start_time) * 1000)}ms')
        logger.info(f'Ping command received from {ctx.author.id}. Latency: {round((end_time - start_time) * 1000)}ms')

