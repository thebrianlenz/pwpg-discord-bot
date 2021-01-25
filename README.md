# PWPG Discord Bot
It's a discord bot.

This is a Discord bot made using the [discord.py API wrapper](https://github.com/Rapptz/discord.py) for Python. It's main goal is for use on the PWPG Discord server.

## Features
- Role Manager: Currently tries to replace/augment some role and group management for various games and collections of users.
- Stats Manager: Tracks reaction and command usage on the server


# Installation and Usage

Install the the python dependencies in requirements.txt:
`pip install -r requirements.txt`
or, to make a local install of the packages:
`pip install -r requirements.txt --user`

Create an application and bot using the [Discord developer portal](link). Use the token to populate a `config.ini` file in the root directory. If you will be using the Reflector module, figure it out on your own until I feel like explaining it, or just disable it as a default module.

config.ini format:

```ini
[main]
token = # Token for the bot

# PRAW and AWS are required for the Reflector cog
[praw]
reddit_client_id =
reddit_client_secret =

[aws]
access_key_id =
secret_access_key =
bucket_name =
```

# Roadmap?

- Secret Hitler
- multiple people are typing response
- "async with typing" for longer computations
- refactor file structure, including cogs/utils

