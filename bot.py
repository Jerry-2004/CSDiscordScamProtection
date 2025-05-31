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

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    db.create_tables()

    channel_id = 1378353998482116720
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("Database successfully initialised at */data/bot_data.db")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)
