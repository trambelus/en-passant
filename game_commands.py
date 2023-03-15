# Implements game-related slash commands.

import logging
import random
from typing import Dict

import interactions
from interactions.utils.get import get

from client_session import ClientGameSession, board_to_emoji
from client_options import ClientOptions
from command_defs import commands

logger = logging.getLogger(__name__)

def register_game_commands(client: interactions.Client, active_games: Dict[int, ClientGameSession]):
    '''Implement and implicitly register game-related slash commands.'''
    # TODO: use some kind of manager to handle the active games instead of a dict
    # Maybe a singleton class?

    logger.info("Registering game commands")

    # Decorators take care of registering the commands with the interactions library.
    @client.command(
        name=commands['game_commands']['new']['name'],
        description=commands['game_commands']['new']['description'],
        scope=commands['game_commands']['GUILD_ID'],
        options=[
            interactions.Option(
                name='color',
                description='The color to play as',
                type=interactions.OptionType.STRING,
                required=True,
                choices=[
                    interactions.Choice(
                        name='White',
                        value='white'
                    ),
                    interactions.Choice(                            
                        name='Black',
                        value='black'
                    ),
                    interactions.Choice(
                        name='Random',
                        value='random'
                    )
                ]
            ),
            interactions.Option(
                name='vs',
                # description='The opponent to play against ("bot" to play against AI, or mention a user to play against them)',
                description='Mention a user to play against them',
                type=interactions.OptionType.STRING,
                required=True,
            ),                    
        ]
    )
    async def new_game(ctx: interactions.CommandContext, color: str, vs: str) -> None:        
        '''Create a new game.'''
        try:
            author_nick = ctx.author.nick if ctx.author.nick else ctx.author.user.username
            # Determine the opponent
            # if vs != 'bot' and not vs.startswith('<@') and not vs.endswith('>'):
            if not vs.startswith('<@') and not vs.endswith('>'):
                # await ctx.send(content='Invalid opponent! Please mention a user or specify "bot".')
                await ctx.send(content='Invalid opponent! Please mention a user.')
                return
            if vs == 'bot':
                vs_nick = 'En Passant Bot'
                vs_member = {'id': None, 'nick': vs_nick, 'user': {'username': vs_nick}}
            else:
                vs_id = vs[2:-1]
                logger.debug(f'Fetching nickname for user {vs_id}')
                vs_member = await get(client, interactions.Member, parent_id=ctx.guild_id, object_id=vs_id)
                vs_nick = vs_member.nick if vs_member.nick else vs_member.user.username
            if color == 'random':
                color = random.choice(['white', 'black'])

            # Create a new Discord thread in the current channel to handle the game
            name = f'{author_nick} vs {vs_nick}'
            thread = await ctx.channel.create_thread(name=name)

            # Define client options
            client_options_dict = {
                'author': ctx.author,
                'opponent': vs_member,
                'author_is_white': color == 'white',
                'author_nick': author_nick,
                'opponent_nick': vs_nick,
                'players': 1 if vs == 'bot' else 2,
                'notation': 'san',
                'ping': 'none',
                'channel_id': thread.id,
                'name': name,
            }
            client_options = ClientOptions(**client_options_dict)
            # TODO: load unspecified client options as user options from database

            # Create a new GameSession
            game_session = ClientGameSession(client_options=client_options)

            # Add the GameSession to the list of active games
            active_games[thread.id] = game_session
            # Send response
            await ctx.send(content=f'New game started in {thread.mention}!')
            # Send the board
            msg_content = game_session.new_game()
            await thread.send(content=msg_content)
            # TODO: modal to specify AI game or human game, and if human game, who to play against, and what color to play as, and whether to ping them
        except Exception as e:
            logger.exception(e)
            await ctx.send(content='Error creating new game!')
            if thread:
                await thread.delete()

    @client.command(
        name=commands['game_commands']['move']['name'],
        description=commands['game_commands']['move']['description'],
        scope=commands['game_commands']['GUILD_ID'],
        options=[
            interactions.Option(
                name='move',
                description='The move to make, in SAN format (e.g. e4, Nf3, etc.) or UCI format (e.g. e2e4, g1f3, etc.)',
                type=interactions.OptionType.STRING,
                required=True
            ),
        ],
    )
    async def make_move(ctx: interactions.CommandContext, move: str) -> None:
        # Get the game session from the list of active games
        try:
            game_session = active_games[ctx.channel_id]
        except KeyError:
            await ctx.send(content='No active game in this channel!')
            # TODO: support resuming games from channel data (e.g. if the bot restarts)
            return
        
        # Check if the game is over before making the move
        if game_session.is_game_over:
            await ctx.send(content='Game is already over!')
            return
        # Make the move
        response = game_session.make_move(move, ctx.author)
        # Send the response
        await ctx.send(content=response)
        # Check if the game is over after making the move
        if game_session.is_game_over:
            # Lock the thread
            await ctx.channel.lock(reason='Game over')
            # Remove the game from the list of active game
            del active_games[ctx.channel_id]
