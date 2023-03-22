from interactions import Client
from .admin_commands import refresh_emoji_names, register_admin_commands
from .game_commands import register_game_commands
from .command_definitions import commands

def register_commands(client: Client):
    '''
    Register all the commands with the client
    '''
    register_admin_commands(client)
    register_game_commands(client)
