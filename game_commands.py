# Implements game-related slash commands.

import logging
import random
from base64 import b64decode, b64encode
from json import dumps, loads

import interactions
from interactions import Button, ButtonStyle
from interactions.utils.get import get
from interactions.utils.utils import spread_to_rows

from client_options import ClientOptions
from client_session import ClientGameSession, board_to_emoji
from client_utils import cleanup, get_last_moves
from command_defs import commands
from game_manager import game_manager, save_after

logger = logging.getLogger(__name__)

def register_game_commands(client: interactions.Client):
    '''Implement and implicitly register game-related slash commands.'''

    logger.info("Registering game commands")

    # Decorators take care of registering the commands with the interactions library.
    @client.command(**commands['game_commands']['new'])
    @save_after
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
                'author_id': ctx.author.id,
                'opponent_id': vs_member.id,
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

            # Register the session with the game manager
            game_manager.add_game(thread.id, game_session)

            # Send response in the current channel
            await ctx.send(content=f'New game started in {thread.mention}!')

            # Send the board in the thread
            msg_content = game_session.new_game()
            await thread.send(content=msg_content)

            # TODO: modal to specify AI game or human game, and if human game, who to play against, and what color to play as, and whether to ping them
            # Modals are shiny and new, and current bots probably don't use them, so it would be a nice touch.
        except Exception as e:
            logger.exception(e)
            await ctx.send(content='Error creating new game!')
            if thread:
                await thread.delete()
    
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
        
        await make_move(ctx, move, game_session)

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
