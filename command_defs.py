# This file contains the commands for the bot.
# Was originally JSON, but it's a Python dict now because subsituting variables is easier.
# Also might be easier to define options compatible with discord interactions.

from config import HOME_GUILD_ID, ADMIN_CHANNEL_ID

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
            "description": "Start a new game."
        },
        "option": {
            "name": "option",
            "description": "Set an option, e.g. /option level 5"
        },
        "list_options": {
            "name": "list_options",
            "description": "List all game options."
        },
        "move": {
            "name": "move",
            "description": "Make a move, e.g. e4 or e2e4"
        },
        "moves": {
            "name": "moves",
            "description": "Show a (TBD: clickable) list of available legal moves."
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