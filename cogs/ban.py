from discord.ext import commands
import discord
import asyncio

import constants
import db
from decorators import is_moderator, is_whitelisted
class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ban')
    @commands.check(is_moderator())
    @commands.check(is_whitelisted())
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

            # Save ban to DB
            db.record_ban(user_id, ctx.guild.id, ctx.author.id, reason, evidence)

            # -- Broadcast ban to other whitelisted guilds --

            print ("Initiating global ban vote")

            whitelisted_ids = db.get_all_whitelisted_guilds(exclude_guild_id=ctx.guild.id)

            print (f"Whitelisted guilds (excluding current): {whitelisted_ids}")
            # stores the icon of the server to use in the embed message
            origin_guild_icon = ctx.guild.icon.url if ctx.guild.icon else None

            for guild_id in whitelisted_ids:
                print(guild_id)
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    print(f"Sending message to {str(guild)}")
                    if guild is None:
                        guild = await self.bot.fetch_guild(int(guild_id))
                except discord.NotFound:
                    print(f"❌ Guild {guild_id} not found (bot likely not in it).")
                    continue
                except discord.Forbidden:
                    print(f"❌ Forbidden: No permission to access guild {guild_id}.")
                    continue
                except discord.HTTPException as e:
                    print(f"❌ HTTP error fetching guild {guild_id}: {e}")
                    continue

                channel = discord.utils.get(guild.text_channels, name=constants.OPERATING_CHANNEL_NAME)
                if channel is None:
                    print(f"Channel not found in {guild_id}")
                    continue  # Will skip servers that have renamed or deleted the text channel

                embed = discord.Embed(
                    title="⚠️ Cross-Server Ban Vote Requested",
                    description=(
                        f"**User:** `{user.display_name}` (`{user.id}`)\n"
                        f"**Reason:** `{reason}`\n"
                        f"**Evidence:** `{evidence}`\n\n"
                        f"React with ✅ to support the ban, ❌ to reject."
                    ),
                    color=discord.Color.orange()
                )
                if origin_guild_icon:
                    embed.set_thumbnail(url=origin_guild_icon)

                embed.set_footer(text=f"Ban initiated from: {ctx.guild.name} - ({ctx.guild.id})")

                vote_msg = await channel.send(embed=embed)
                await vote_msg.add_reaction("✅")
                await vote_msg.add_reaction("❌")

        except asyncio.TimeoutError:
            await ctx.send("Timeout: ban command cancelled.")


async def setup(bot):
    await bot.add_cog(Ban(bot))