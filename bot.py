# Main logic for the bot

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=";", intents=intents)


# Decorator function to block commands if the server is not in the whitelisted table
def is_whitelisted():
    async def predicate(ctx):
        # ctx.guild is None if the command is used in a DM
        if ctx.guild is None:
            return False

        return db.is_guild_whitelisted(ctx.guild.id)

    return commands.check(predicate)
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    db.create_tables()

    channel_id = 1378353998482116720
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("Database successfully initialised at */data/bot_data.db")

@bot.command()
@is_whitelisted()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)
