# Implements game-related slash commands.

import logging
import random
from base64 import b64decode, b64encode
from json import dumps, loads
from chess import BLACK, WHITE

import interactions
from interactions import Button, ButtonStyle
from interactions.utils.utils import spread_to_rows

from client import (ClientGameSession, ClientOptions, cleanup, game_manager,
                    save_after)
from game import Player

from .command_definitions import commands

logger = logging.getLogger(__name__)

def register_game_commands(client: interactions.Client):
    '''Implement and implicitly register game-related slash commands.'''

    logger.info("Registering game commands")

    async def new_game_pvp(ctx: interactions.CommandContext, vs_user: interactions.User, color: str = 'random', ranked: bool = True, time_control: str = None) -> interactions.Channel:
        author_nick = ctx.author.nick if ctx.author.nick else ctx.author.user.username
        # Determine the opponent
        if vs_user is None:
            await ctx.send(content='Invalid opponent! Please mention a user.')
            return
        else:
            vs_nick = vs_user.nick if vs_user.nick else vs_user.user.username

        # Check if the opponent is a bot (not allowed, that's what /new pvai is for)
        if vs_user.bot:
            await ctx.send(content='Invalid opponent! You can\'t play a bot in a PvP game.')
            return

        # Determine the color
        if color == 'random':
            color = random.choice(['white', 'black'])

        # Create a new Discord thread in the current channel to handle the game
        name = f'{author_nick} vs {vs_nick}'
        game_channel = await ctx.channel.create_thread(name=name)

        # Define client options
        client_options_dict = {
            'author': Player(ctx.author.id, author_nick, WHITE if color == 'white' else BLACK),
            'opponent': Player(vs_user.id, vs_nick, BLACK if color == 'white' else WHITE),
            'players': 2,
            'notation': 'san',
            'ping': 'none',
            'channel_id': game_channel.id,
            'name': name,
        }
        client_options = ClientOptions(**client_options_dict)
        # TODO: load unspecified client options as user options from database

        # Create a new GameSession
        game_session = ClientGameSession(client_options=client_options)

        # Register the session with the game manager
        game_manager.add_game(game_channel.id, game_session)

        # Send response in the current channel
        await ctx.send(content=f'New game started in {game_channel.mention}!')

        # Send the board in the thread
        msg_content = game_session.new_game()
        await game_channel.send(content=msg_content)

        # TODO: modal to specify AI game or human game, and if human game, who to play against, and what color to play as, and whether to ping them
        # Modals are shiny and new, and current bots probably don't use them, so it would be a nice touch.
        return game_channel

    async def new_game_pvai(ctx: interactions.CommandContext, level: str, color: str = 'random', ranked: bool = True, time_control: str = None) -> interactions.Channel:
        await ctx.send(content='Not implemented yet! Please use the `/new pvp` command to play against a human opponent.')
        return None

    # Decorators take care of registering the commands with the interactions library.
    @client.command(**commands['game_commands']['new'])
    @save_after
    async def new_game(ctx: interactions.CommandContext, sub_command: str, vs: interactions.Member = None, level: str = 'random') -> None:        
        '''Create a new game.'''
        game_channel = None
        try:
            # Check if this is a thread
            if ctx.channel.type in [interactions.ChannelType.PUBLIC_THREAD, interactions.ChannelType.PRIVATE_THREAD]:
                await ctx.send(content='You cannot create a new game in a thread! Try creating a new game in the channel where this thread was created.')
                return
            
            # Check if this is a DM
            if ctx.channel.type == interactions.ChannelType.DM:
                await ctx.send(content='You cannot create a new game in a DM! Try creating a new game in a server.')
                return

            # Is this a PvP game?
            if sub_command == 'pvp':
                game_channel = await new_game_pvp(ctx, vs, level)
                return
            
            # Is this a PvAI game?
            elif sub_command == 'pvai':
                game_channel = await new_game_pvai(ctx, level)
                return
            
            else:
                await ctx.send(content='Invalid subcommand! Not sure what you\'re trying to do.')
                logger.error('Invalid subcommand %s for /new command.', sub_command)
                return
        # pylint: disable=broad-except
        except Exception as ex:
            logger.exception(ex)
            await ctx.send(content='Error creating new game!')
            if game_channel:
                await game_channel.delete()
    
    @client.command(**commands['game_commands']['move'])
    async def move_command(ctx: interactions.CommandContext, move: str) -> None:
        # Get the game session from the list of active games
        try:
            game_session = game_manager[ctx.channel_id]
        except KeyError:
            # Check if we're in a thread, to provide a more helpful error message
            if ctx.channel.type in [interactions.ChannelType.PUBLIC_THREAD, interactions.ChannelType.PRIVATE_THREAD]:
                # First see if the bot sent a message containing a board in this thread
                # if ctx.channel.last_message_id:
                #     if await get_last_moves(ctx.channel):
                #         logger.info(f'Attempting to resume game from last message in thread {ctx.channel_id}')
                #         await ctx.send('I spotted a game up there, but I don\'t have enough information to resume it. Please use the `/resume` command to resume the game from a specific position, or use the `/new` command to start a new game.')
                #         return # TODO

                await ctx.send(content='No active game found in this thread! If you want to try resuming a game from a specific position, please use the `/resume` command.')
            else:
                await ctx.send(content='You can only make moves in a game thread! To start a new game, use the `/new` command.')
            return
        
        await make_move(ctx, game_session, move)

    @save_after
    async def make_move(ctx: interactions.CommandContext | interactions.ComponentContext, game_session: ClientGameSession, move: str) -> None:
        '''Make a move in the current game.'''
        
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
            try:
                await ctx.channel.lock(reason='Game over')
            except Exception as e:
                logger.exception(e)
                await ctx.send(content='Error locking thread!')
            # Remove the game from the list of active game
            game_manager.remove_game(ctx.channel_id)
    
    @client.command(**commands['game_commands']['moves'])
    async def moves(ctx: interactions.CommandContext) -> None:
        try:
            game_session = game_manager[ctx.channel_id]
        except KeyError:
            await ctx.send(content='No active game found in this channel!')
            return
        moves_san = [game_session.board.san(move) for move in game_session.board.legal_moves]
        moves_san.sort(key=str.casefold)
        if len(moves_san) > 0:
            # await ctx.send(content=f'Legal moves: **{"**, **".join(moves_san)}**')
            buttons = [Button(style=ButtonStyle.SECONDARY, label=move, custom_id=b64encode(dumps({'type': 'move', 'channel_id': str(ctx.channel_id), 'value': move}).encode('utf-8')).decode('utf-8')) for move in moves_san]
            await ctx.send(content='Legal moves (in alphabetical order):', components=spread_to_rows(*buttons))
        else:
            await ctx.send(content='No legal moves! (Stalemate or checkmate)')
    
    @client.event(name='on_component')
    async def on_component(ctx: interactions.ComponentContext) -> None:
        '''Handle button presses.'''
        button_context = loads(b64decode(ctx.component.custom_id).decode('utf-8'))
        # if ctx.component.custom_id == 'new_game':
        #     await new_game(ctx)
        # elif ctx.component.custom_id == 'moves':
        #     await moves(ctx)
        if button_context['type'] == 'move':
            channel_id = button_context['channel_id']
            try:
                game_session = game_manager[channel_id]
            except KeyError:
                await ctx.send(content='No active game found in this channel!')
                return
            await make_move(ctx, game_session, button_context['value'])

    @client.command(**commands['game_commands']['lock'])
    async def lock_thread(ctx: interactions.CommandContext) -> None:
        await ctx.send(content='Locking thread...')
        await ctx.channel.lock(reason='User requested lock')
        await ctx.send(content='Thread locked!')

    @client.command(**commands['game_commands']['cleanup'])
    async def _cleanup(ctx: interactions.CommandContext, message_id: int) -> None:
        if await cleanup(client, message_id, ctx.channel_id):
            # If the cleanup was successful, send a confirmation message (ephemeral)
            await ctx.send(content='Message cleaned up!', ephemeral=True)
        else:
            # If the cleanup failed, send an error message (ephemeral)
            await ctx.send(content='Failed to clean up message!', ephemeral=True)
