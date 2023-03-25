# This file contains the commands for the bot.
# Was originally JSON, but it"s a Python dict now because subsituting variables is easier.
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
            "description": "Reupload all emoji to the home guild (WARNING: may be 429ed one hour if run more than once)."
        },
        "refresh_emoji_cache": {
            "name": "refresh_emoji_cache",
            "description": "Refresh the emoji cache."
        },
        "shutdown": {
            "name": "shutdown",
            "description": "Shutdown the bot."
        },
        "eval": {
            "name": "eval",
            "description": "Evaluate a Python expression. Please don't use this command unless you know what you're doing.",
            "default_member_permissions": Permissions.ADMINISTRATOR,
            "options": [
                Option(
                    name="expression",
                    description="The Python expression to evaluate",
                    type=OptionType.STRING,
                    required=True
                )
            ]
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
                    name="pvp",
                    description="Play against another player",
                    type=OptionType.SUB_COMMAND,
                    options=[
                        Option(
                            name="vs",
                            description="Mention a user to play against them",
                            type=OptionType.USER,
                            required=True,
                        ),
                        Option(
                            name="color",
                            description="The color to play as (defaults to random)",
                            type=OptionType.STRING,
                            required=False,
                            choices=[
                                Choice(name="White", value="white"),
                                Choice(name="Black", value="black"),
                                Choice(name="Random", value="random")
                            ]
                        ),
                        Option(
                            name="time",
                            description="Time control, e.g. 5+5. Defaults to unlimited time.",
                            type=OptionType.STRING,
                            required=False,
                        ),
                        Option(
                            name="rated",
                            description="Whether the game should be rated (defaults to true)",
                            type=OptionType.BOOLEAN,
                            required=False,
                        ),
                    ]
                ),
                Option(
                    name="pvai",
                    description="Play against the AI",
                    type=OptionType.SUB_COMMAND_GROUP,
                    options=[
                        Option(
                            name="elo",
                            description="Play against the AI at a specific Elo rating",
                            type=OptionType.SUB_COMMAND,
                            options=[
                                Option(
                                    name="level",
                                    description="The rating to play against (or \"random\" to play against a random level)",
                                    type=OptionType.STRING,
                                    required=True,
                                    choices=[
                                        Choice(name="1100", value="1100"),
                                        Choice(name="1200", value="1200"),
                                        Choice(name="1300", value="1300"),
                                        Choice(name="1400", value="1400"),
                                        Choice(name="1500", value="1500"),
                                        Choice(name="1600", value="1600"),
                                        Choice(name="1700", value="1700"),
                                        Choice(name="1800", value="1800"),
                                        Choice(name="1900", value="1900"),
                                        Choice(name="random", value="random")
                                    ]
                                ),
                                Option(
                                    name="color",
                                    description="The color to play as (defaults to random)",
                                    type=OptionType.STRING,
                                    required=False,
                                    choices=[
                                        Choice(name="White", value="white"),
                                        Choice(name="Black", value="black"),
                                        Choice(name="Random", value="random")
                                    ]
                                ),
                                Option(
                                    name="time",
                                    description="Time control, e.g. 5+5. Defaults to unlimited time.",
                                    type=OptionType.STRING,
                                    required=False,
                                ),
                                Option(
                                    name="rated",
                                    description="Whether the game should be rated (defaults to true)",
                                    type=OptionType.BOOLEAN,
                                    required=False,
                                ),
                            ]
                        ),
                        Option(
                            name="placement",
                            description="Play three placement games against the AI to set your initial Elo rating",
                            type=OptionType.SUB_COMMAND,
                        ),
                    ]
                ),
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
                    name="message_id",
                    description="The ID of the message to clean up",
                    type=OptionType.STRING,
                    required=True
                )
            ]
        },
        "option": {
            "name": "option",
            "description": "Set an option, e.g. /option format san",
            "options": [
                Option(
                    name="format",
                    description="Move format (UCI or SAN)",
                    type=OptionType.SUB_COMMAND,
                    options=[
                        Option(
                            name="format",
                            description="Move format (UCI or SAN)",
                            type=OptionType.STRING,
                            required=True,
                            choices=[
                                Choice(name="UCI", value="uci"),
                                Choice(name="SAN", value="san")
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
                    name="move",
                    description="Your move in SAN format (e.g. e4, Nf3) or UCI format (e.g. e2e4, g1f3)",
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
            "description": "Request to undo the last move.",
            "scope": SCOPE,
            "options": [
                Option(
                    name="request",
                    description="Request to undo the last move",
                    type=OptionType.SUB_COMMAND,
                ),
                Option(
                    name="cancel",
                    description="Cancel your undo request",
                    type=OptionType.SUB_COMMAND,
                ),
                Option(
                    name="accept",
                    description="Accept your opponent\'s undo request",
                    type=OptionType.SUB_COMMAND,
                ),
                Option(
                    name="decline",
                    description="Decline your opponent\'s undo request",
                    type=OptionType.SUB_COMMAND,
                ),
            ]
        },
        "draw": {
            "name": "draw",
            "description": "Request a draw.",
            "scope": SCOPE,
            "options": [
                Option(
                    name="request",
                    description="Request a draw",
                    type=OptionType.SUB_COMMAND,
                ),
                Option(
                    name="cancel",
                    description="Cancel your draw request",
                    type=OptionType.SUB_COMMAND,
                ),
                Option(
                    name="accept",
                    description="Accept your opponent\'s draw request",
                    type=OptionType.SUB_COMMAND,
                ),
                Option(
                    name="decline",
                    description="Decline your opponent\'s draw request",
                    type=OptionType.SUB_COMMAND,
                ),
            ]
        },
        "resign": {
            "name": "resign",
            "description": "Resign the game."
        }
    },
    "user_commands": {
        "GUILD_ID": int(HOME_GUILD_ID),
        "CHANNEL_ID": None,
        "help": {
            "name": "help",
            "description": "Show help for a command, e.g. /help new",
            "scope": SCOPE,
            "options": [
                Option(
                    name="topic",
                    description="The topic to show help for",
                    type=OptionType.STRING,
                    required=False
                )
            ]
        },
        "ping": {
            "name": "ping",
            "description": "Ping the bot and get the latency.",
            "scope": SCOPE,
        },
    }
}