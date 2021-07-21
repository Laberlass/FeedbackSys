from asyncio import sleep
from datetime import datetime
from glob import glob

from discord import Intents, Embed, File, DMChannel
from discord import HTTPException, Forbidden
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Context
from discord.ext.commands import (CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown, RoleNotFound, MissingPermissions)

from discord.ext.commands import command, when_mentioned_or, has_permissions

from pathlib import Path
from ..db import db

OWNER_IDS = [504641949068689430]
COGS = [p.stem for p in Path(".").glob("./lib/cogs/*.py")]
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument)


def get_prefix(bot, message):
    try:
        prefix = db.field("SELECT Prefix FROM guilds WHERE GuildID = ?", message.guild.id)

    except:
        prefix = "!"
    return when_mentioned_or(prefix)(bot, message)


class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"  {cog} Cog is Ready.")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])


class Bot(BotBase):
    def __init__(self):
        self.ready = False
        self.cogs_ready = Ready()
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)
        super().__init__(
            command_prefix=get_prefix,
            owner_ids=OWNER_IDS,
            case_insensitive=True,
            help_command=None,
            intents=Intents.all(),
            )

    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f"  {cog} Cog Loaded")

        print("Setup Complete.")

    def update_db(self):
        db.multiexec("INSERT OR IGNORE INTO guilds (GuildID) VALUES (?)",
					 ((guild.id,) for guild in self.guilds))

    def run(self, version):
        self.VERSION = version

        print("Running setup...")
        self.setup()

        with open("./lib/bot/token.0", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()

        print("Running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                if ctx.command is not None and ctx.guild is not None:
                    await self.invoke(ctx)

            else:
                await ctx.send("Im not ready to revieve commands. Please wait a few seconds")

    async def on_connect(self):
        print("Bot connected.")

    async def on_disconnect(self):
        print("Bot disconnected.")

    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")

        raise

    async def on_command_error(self, ctx, exc):
        if any([isinstance(exc, error) for error in IGNORE_EXCEPTIONS]):
            pass

        elif isinstance(exc, MissingPermissions):
            await ctx.send("You dont have enough permissions to run this command.")

        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing.")

        elif isinstance(exc, CommandOnCooldown):
            await ctx.send(f"That command is on {str(exc.cooldown.type).split('.')[-1]} cooldown. Try again in {exc.retry_after:,.2f} secs.")

        elif hasattr(exc, "original"):
            if isinstance(exc.original, HTTPException):
                await ctx.send("Unable to send message.")

            if isinstance(exc.original, Forbidden):
                await ctx.send("I do not have permission to do that.")

            else:
                raise exc.original

        else:
            raise exc



    async def on_ready(self):
        if not self.ready:
            self.scheduler.start()

            self.update_db()

            while not self.cogs_ready.all_ready():
                await sleep(0.5)

            self.ready = True
            print("  Bot ready.")

        else:
            print("Bot reconnected.")

    async def close(self):
        print("Shutting down...")
        db.commit()
        await super().close()

bot = Bot()
