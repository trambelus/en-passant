# This file contains the commands for the bot.
# Was originally JSON, but it's a Python dict now because subsituting variables is easier.
# Also might be easier to define options compatible with discord interactions.

from interactions import Option, OptionType, Choice, Permissions

from config import HOME_GUILD_ID, ADMIN_CHANNEL_ID

SCOPE = int(HOME_GUILD_ID)

commands = {
    "admin_commands": {
        "GUILD_ID": int(HOME_GUILD_ID),
        "CHANNEL_ID": int(ADMIN_CHANNEL_ID),
        "ping": {
            "name": "ping",
            "description": "Ping the bot."
        },
        "guilds": {
            "name": "guilds",
            "description": "List all guilds the bot is in."
        },
        "join_request": {
            "name": "join_request",
            "description": "Generate a join request link for a guild."
        },
        "stats": {
            "name": "stats",
            "description": "Show some stats about the bot."
        },
        "reupload_emoji": {
            "name": "reupload_emoji",
            "description": "Reupload all emojis to the home guild (WARNING: may be 429 rate-limited to an hour cooldown if run more than once)."
        },
        "refresh_emoji_cache": {
            "name": "refresh_emoji_cache",
            "description": "Refresh the emoji cache."
        },
        "shutdown": {
            "name": "shutdown",
            "description": "Shutdown the bot."
        }
    },
    "game_commands": {
        "GUILD_ID": int(HOME_GUILD_ID),
        "CHANNEL_ID": None,
        "new": {
            "name": "new",
            "description": "Start a new game.",
            "scope": SCOPE,
            "options": [
                Option(
                    name='color',
                    description='The color to play as',
                    type=OptionType.STRING,
                    required=True,
                    choices=[
                        Choice(name='White', value='white'),
                        Choice(name='Black', value='black'),
                        Choice(name='Random', value='random')
                    ]
                ),
                Option(
                    name='vs',
                    description='Mention a user to play against them',
                    #description='Mention a user to play against them, or "bot" to play against AI',
                    type=OptionType.STRING,
                    required=True,
                ),
                Option(
                    name='time',
                    description='Time control, e.g. 5+5. Defaults to unlimited time.',
                    type=OptionType.STRING,
                    required=False,
                )
            ]
        },
        "lock": {
            "name": "lock",
            "description": "Lock the current game thread",
            "scope": SCOPE,
            "default_member_permissions": Permissions.MANAGE_THREADS,
        },
        "cleanup": {
            "name": "cleanup",
            "description": "Clean up the bot's most recent messages in the current channel.",
            "scope": SCOPE,
            "default_member_permissions": Permissions.MANAGE_THREADS,
            "options": [
                Option(
                    name='message_id',
                    description='The ID of the message to clean up',
                    type=OptionType.STRING,
                    required=True
                )
            ]
        },
        "option": {
            "name": "option",
            "description": "Set an option, e.g. /option level 5",
            "options": [
                Option(
                    name='format',
                    description='Move format (UCI or SAN)',
                    type=OptionType.SUB_COMMAND,
                    options=[
                        Option(
                            name='format',
                            description='Move format (UCI or SAN)',
                            type=OptionType.STRING,
                            required=True,
                            choices=[
                                Choice(name='UCI', value='uci'),
                                Choice(name='SAN', value='san')
                            ]
                        )
                    ]
                ),
            ]
        },
        "list_options": {
            "name": "list_options",
            "description": "List all game options."
        },
        "move": {
            "name": "move",
            "description": "Make a move, e.g. e4 or e2e4",
            "scope": SCOPE,
            "options": [
                Option(
                    name='move',
                    description='Your move in SAN format (e.g. e4, Nf3) or UCI format (e.g. e2e4, g1f3)',
                    type=OptionType.STRING,
                    required=True
                ),
            ]
        },
        "moves": {
            "name": "moves",
            "description": "Show a list of available legal moves.",
            "scope": SCOPE,
        },
        "undo": {
            "name": "undo",
            "description": "Request to undo the last move. A human player can accept or decline the request with /accept or /decline."
        },
        "draw": {
            "name": "draw",
            "description": "Request a draw. A human player can accept or decline the request with /accept or /decline."
        },
        "resign": {
            "name": "resign",
            "description": "Resign the game."
        },
        "accept": {
            "name": "accept",
            "description": "Accept a draw or undo request."
        },
        "decline": {
            "name": "decline",
            "description": "Decline a draw or undo request."
        }
    }
}