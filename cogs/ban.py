from discord.ext import commands
import discord
import asyncio

import db
from decorators import is_moderator
class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ban')
    @commands.check(is_moderator())
    async def ban(self, ctx, user_id: int):
        # Fetch user from guild
        user = ctx.guild.get_member(user_id)
        if user is None:
            await ctx.send(f"User with ID {user_id} not found in this server.")
            return

        await ctx.send(f"Preparing to ban user {user.display_name} (ID: {user_id}).")
        await ctx.send("Please state the reason for the ban:")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reason_msg = await self.bot.wait_for('message', check=check, timeout=120)
            reason = reason_msg.content

            await ctx.send("Please provide evidence (e.g. message links, screenshots):")
            evidence_msg = await self.bot.wait_for('message', check=check, timeout=120)
            evidence = evidence_msg.content

            # Confirmation prompt
            await ctx.send(f"Ban user {user.display_name} for reason:\n**{reason}**\nEvidence:\n{evidence}\nType 'confirm' to ban or 'cancel' to abort.")

            confirm_msg = await self.bot.wait_for('message', check=check, timeout=60)
            if confirm_msg.content.lower() != 'confirm':
                await ctx.send("Ban cancelled.")
                return

            # Ban user
            await ctx.guild.ban(user, reason=reason)
            await ctx.send(f"User {user.display_name} has been banned.")

            # Save ban to DB (implement your own db method)
            db.record_ban(user_id, ctx.guild.id, ctx.author.id, reason, evidence)

        except asyncio.TimeoutError:
            await ctx.send("Timeout: ban command cancelled.")


async def setup(bot):
    await bot.add_cog(Ban(bot))