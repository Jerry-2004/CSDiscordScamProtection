from discord.ext import commands
import discord
import asyncio

import constants
import db
from decorators import is_moderator, is_whitelisted


class BanReasonView(discord.ui.View):
    def __init__(self, reasons, author: discord.User, timeout=60):
        super().__init__(timeout=timeout)
        self.selected_reason = None
        self.author = author
        for reason in reasons:
            self.add_item(BanReasonButton(reason))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class BanReasonButton(discord.ui.Button):
    def __init__(self, reason):
        super().__init__(label=reason, style=discord.ButtonStyle.primary)
        self.reason = reason

    async def callback(self, interaction: discord.Interaction):
        view: BanReasonView= self.view
        view.selected_reason = self.reason
        await interaction.response.defer()
        self.view.stop()


class ConfirmView(discord.ui.View):
    def __init__(self, author: discord.User, timeout=60):
        super().__init__(timeout=timeout)
        self.author = author
        self.confirmed = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        await interaction.response.defer()
        self.stop()


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ban')
    @is_moderator()
    @is_whitelisted()
    async def ban(self, ctx, user_id: int):
        # Delete the original command
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        user = ctx.guild.get_member(user_id)
        if user is None:
            await ctx.send(f"User with ID {user_id} not found in this server.", delete_after=5)
            return

        if user.id in (ctx.author.id, self.bot.user.id):
            await ctx.send("You cannot ban yourself or the bot.", delete_after=5)
            return

        reason_embed = discord.Embed(
            title="🔨 Ban Initialization",
            description=f"Preparing to ban: **{user.display_name}**\n\nPlease select a reason below:",
            color=discord.Color.orange()
        )
        reason_view = BanReasonView(constants.BAN_REASONS, author=ctx.author)
        reason_msg = await ctx.send(embed=reason_embed, view=reason_view)
        await reason_view.wait()

        if reason_view.selected_reason is None:
            await reason_msg.edit(embed=discord.Embed(title="⏱️ Timeout", description="No reason selected in time.",
                                                      color=discord.Color.red()), view=None)
            await asyncio.sleep(5)
            await reason_msg.delete()
            return

        reason = reason_view.selected_reason
        await reason_msg.delete()

        evidence_embed = discord.Embed(
            title="🧾 Provide Evidence",
            description=f"You selected reason: **{reason}**\n\nPlease upload screenshots or paste message links.",
            color=discord.Color.orange()
        )
        evidence_prompt = await ctx.send(embed=evidence_embed)

        try:
            evidence_msg = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=120
            )
            evidence_text = evidence_msg.content
            image_urls = [
                a.url for a in evidence_msg.attachments
                if a.content_type and a.content_type.startswith("image/")
            ]
            await evidence_msg.delete()
            await evidence_prompt.delete()
        except asyncio.TimeoutError:
            await evidence_prompt.edit(
                embed=discord.Embed(title="⏱️ Timeout", description="No evidence submitted in time.",
                                    color=discord.Color.red()))
            await asyncio.sleep(5)
            await evidence_prompt.delete()
            return

        confirm_embed = discord.Embed(
            title="❗ Ban Confirmation",
            description=f"**User:** {user.mention}\n**Reason:** {reason}\n**Evidence:** {evidence_text}",
            color=discord.Color.red()
        )
        if image_urls:
            confirm_embed.set_image(url=image_urls[0])
            if len(image_urls) > 1:
                confirm_embed.add_field(name="More Images", value="\n".join(image_urls[1:]), inline=False)

        confirm_view = ConfirmView(author=ctx.author)
        confirm_msg = await ctx.send(embed=confirm_embed, view=confirm_view)
        await confirm_view.wait()

        if confirm_view.confirmed:
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
            db.record_ban(user.id, ctx.guild.id, ctx.author.id, reason, evidence_text)
            await confirm_msg.edit(embed=discord.Embed(
                title="✅ User Banned",
                description=f"**{user.mention}** has been banned by {ctx.author.mention}.",
                color=discord.Color.green()
            ), view=None)
        else:
            await confirm_msg.edit(embed=discord.Embed(
                title="❌ Ban Cancelled",
                description="The ban operation was cancelled.",
                color=discord.Color.dark_grey()
            ), view=None)

        # Save ban to DB
        db.record_ban(user_id, ctx.guild.id, ctx.author.id, reason, evidence_text)

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
                    f"**Evidence:** `{evidence_text}`\n\n"
                    f"React with ✅ to support the ban, ❌ to reject."
                ),
                color=discord.Color.orange()
            )
            if image_urls:
                embed.set_image(url=image_urls[0])
            if origin_guild_icon:
                embed.set_thumbnail(url=origin_guild_icon)

            embed.set_footer(text=f"Ban initiated from: {ctx.guild.name} - ({ctx.guild.id})")

            vote_msg = await channel.send(embed=embed)
            await vote_msg.add_reaction("✅")
            await vote_msg.add_reaction("❌")

        # except asyncio.TimeoutError:
        #     await ctx.send("Timeout: ban command cancelled.")


async def setup(bot):
    await bot.add_cog(Ban(bot))