# En Passant
### Another Discord chess bot.

En Passant is a chess bot designed to be lightweight, easy to use, and rich in features.
The two main things that set it apart, feature-wise, are its use of emojis instead of dynamically-generated images, which cuts down on bandwidth requirements; and its use of threads for games in servers, which provides easy accessibility while keeping channel clutter to a minimum.

## Features

More features are planned, but here's what there is so far.

- PvP games: Challenge any user to a game with the `/new pvp` command.
- Cleanup: Admins can easily manage clutter with the `/cleanup` command.
- Persistence: The bot will remember active sessions and user settings even across restarts.

Upcoming features:
- PvAI games: Challenge the bot to play at a level anywhere from 1100 to 1900. Uses the Maia chess bots, so it plays a lot more like a human than Stockfish would.
- Rankings: Players can choose to play ranked games, which will update their Elo score within the pool of the bot's player base within a server.
- Game histories: Games are recorded and can be accessed later. Users can choose whether their own histories are private.
- Game analysis: A Stockfish-based engine on the backend can annotate games after their conclusion, helping players improve their skills.
- Variants: The chess library this bot uses can handle all kinds of game variants, so the bot will too! Chess960 will probably be the first implemented.

## Contributing
Contributions are welcome! Feel free to log a GitHub issue if you have a bug or improvement, or fork the repo and make a pull request if you'd like to make a change or fix a bug yourself.

## License

En Passant is licensed under the GPL 3. Full text is available in [LICENSE.txt](./LICENSE.txt), or wherever else you prefer to look it up.
