from discord.ext import commands
import discord

import db
from decorators import is_moderator


class Servers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='servers')
    # Unsure whether to add check for moderator here. Added for now (TODO)
    @commands.check(is_moderator())
    async def servers(self, ctx):
        whitelisted_guild_ids = db.get_all_whitelisted_guilds()

        if not whitelisted_guild_ids:
            await ctx.send("No whitelisted guilds found.")
            return

        embed = discord.Embed(
            title="Whitelisted Servers",
            color=discord.Color.blue(),
            description="List of all servers whitelisted to use this bot."
        )

        for guild_id in whitelisted_guild_ids:
            guild = self.bot.get_guild(guild_id)
            if guild:
                embed.add_field(name=guild.name, value=f"ID: {guild_id}", inline=False)
            else:
                embed.add_field(name="Unknown Server", value=f"ID: `{guild_id}` (not in cache)", inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Servers(bot))