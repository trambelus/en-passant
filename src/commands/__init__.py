from interactions import Client
from .admin_commands import register_admin_commands
from .game_commands import register_game_commands
from .user_commands import register_user_commands
from .command_definitions import commands
from .command_utils import *

def register_commands(client: Client):
    '''
    Register all the commands with the client
    '''
    register_admin_commands(client)
    register_game_commands(client)
    register_user_commands(client)