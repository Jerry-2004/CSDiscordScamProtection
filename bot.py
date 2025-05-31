# Main logic for the bot

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

import constants
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

    MOD_CHANNEL_NAME = constants.OPERATING_CHANNEL_NAME
    for guild in bot.guilds:
        if not db.is_guild_whitelisted(guild.id):
            continue # skips guilds not whitelisted

        mod_channel = discord.utils.get(guild.text_channels, name=MOD_CHANNEL_NAME)

        if mod_channel is None:
            # Create mod-only channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                # Allow users with Manage Messages permission to see channel
            }

            # Finds all roles with manage_messages permission to add them explicitly
            for role in guild.roles:
                if role.permissions.manage_messages:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            mod_channel = await guild.create_text_channel(
                MOD_CHANNEL_NAME,
                overwrites=overwrites,
                reason="Creating mod-only channel for scam reports."
            )
            await mod_channel.send("Mod channel created - bot is online.")

        else:
            # Channel exists, so just send bot online message
            await mod_channel.send("Bot is online.")
@bot.command()
@is_whitelisted()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)
