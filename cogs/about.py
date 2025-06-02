from discord.ext import commands
import discord

import db
from decorators import is_moderator

class About(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='about')
    # TODO - unsure whether to add a check for moderator here
    @is_moderator()
    async def about(self, ctx):

        guild = ctx.guild

        if not guild:
            return

        embed = discord.Embed(
            title="About",
            color=discord.Color.blue(),
            description="About this bot and discord ToS."
        )

        embed.add_field(name="About description coming soon", value=f"Will work on tomorrow", inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(About(bot))