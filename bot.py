import os
import asyncio
import logging
from contextlib import suppress

import discord
from discord.ext import commands
import aiohttp

import config
from cogs.utils.database import Database


log = logging.getLogger("discord")
log.setLevel(logging.WARNING)

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")

handler.setFormatter(
    logging.Formatter(
        '{"message": "%(message)s", "level": "%(levelname)s", "time": "%(asctime)s"}'
    )
)

log.addHandler(handler)


class Bot(commands.Bot):
    """A subclass of discord.ext.commands.Bot."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client_session = None
        self.DB = Database()

    @classmethod
    def create(cls) -> commands.Bot:
        """Create and return an instance of a Bot."""
        loop = asyncio.get_event_loop()

        intents = discord.Intents.all()
        intents.dm_typing = False
        intents.webhooks = False
        intents.integrations = False

        return cls(
            loop=loop,
            command_prefix=commands.when_mentioned_or("."),
            activity=discord.Game(name="Tax Evasion Simulator"),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(everyone=False),
            intents=intents,
            owner_ids=(225708387558490112,),
        )

    def load_extensions(self) -> None:
        """Load all extensions."""
        for extension in [f.name[:-3] for f in os.scandir("cogs") if f.is_file()]:
            try:
                self.load_extension(f"cogs.{extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}.\n{e} \n")

    async def get_json(self, url):
        """Gets and loads json from a url.

        session: aiohttp.ClientSession
            A aiohttp client session so that a new one isn't made every request
        url: str
            The url to fetch the json from.
        """
        try:
            async with self.client_session.get(url) as response:
                return await response.json()
        except (
            asyncio.exceptions.TimeoutError,
            aiohttp.client_exceptions.ContentTypeError,
        ):
            return None

    async def close(self) -> None:
        """Close the Discord connection and the aiohttp session."""
        for ext in list(self.extensions):
            with suppress(Exception):
                self.unload_extension(ext)

        for cog in list(self.cogs):
            with suppress(Exception):
                self.remove_cog(cog)

        await super().close()

        if self.client_session:
            await self.client_session.close()

    async def login(self, *args, **kwargs) -> None:
        """Setup the client_session before logging in."""
        self.client_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=6)
        )

        await super().login(*args, **kwargs)


if __name__ == "__main__":
    bot = Bot.create()
    bot.load_extensions()
    bot.run(config.token)
