# Main logic for the bot

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

import constants
import db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix=constants.COMMAND_PREFIX, intents=intents, help_command=None)


async def main():
    await bot.load_extension("cogs.help")
    await bot.load_extension("cogs.ban")
    await bot.load_extension("cogs.servers")
    await bot.load_extension("cogs.about")
    print(bot.commands)
    await bot.start(TOKEN)


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    print("Printing tables")
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
            await mod_channel.send("Mod channel created")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to run this command.")
        print(f"Check failed: {error}")
    else:
        raise error

asyncio.run(main())