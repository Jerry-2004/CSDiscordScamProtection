import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
import os

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

guild_configs = {}  # Simulate DB config per server
ban_records = []    # Simulate DB ban log

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await tree.sync()

@tree.command(name="enable_global_bans", description="Opt in to global bans")
async def enable_global_bans(interaction: discord.Interaction):
    guild_configs[interaction.guild.id] = {"enabled": True, "auto_ban": False, "log_channel_id": None}
    await interaction.response.send_message("✅ This server is now opted into the global ban system.", ephemeral=True)

@tree.command(name="setlogchannel", description="Set the channel for global ban notifications")
@app_commands.describe(channel="The channel to send ban logs to")
async def set_log_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    config = guild_configs.get(interaction.guild.id)
    if not config:
        await interaction.response.send_message("Global bans not enabled. Run /enable_global_bans first.", ephemeral=True)
        return
    config["log_channel_id"] = channel.id
    await interaction.response.send_message(f"📄 Log channel set to {channel.mention}.", ephemeral=True)

@tree.command(name="set_autoban", description="Enable or disable auto banning globally banned users")
@app_commands.describe(enabled="True to auto-ban, False to just notify")
async def set_autoban(interaction: discord.Interaction, enabled: bool):
    config = guild_configs.get(interaction.guild.id)
    if not config:
        await interaction.response.send_message("Global bans not enabled. Run /enable_global_bans first.", ephemeral=True)
        return
    config["auto_ban"] = enabled
    await interaction.response.send_message(f"⚙️ Auto-ban set to {enabled}.", ephemeral=True)

@tree.command(name="globalban", description="Issue a global ban")
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
async def global_ban(interaction: discord.Interaction, user: discord.User, reason: str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You don't have permission to use this.", ephemeral=True)
        return

    if not interaction.attachments:
        await interaction.response.send_message("You must attach at least one image as proof.", ephemeral=True)
        return

    proof_urls = [attachment.url for attachment in interaction.attachments]
    ban_records.append({
        "user_id": user.id,
        "reason": reason,
        "proof": proof_urls,
        "source_guild": interaction.guild.id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

    await interaction.response.send_message(f"🔨 {user.mention} has been globally banned for: {reason}", ephemeral=True)

    for guild in bot.guilds:
        config = guild_configs.get(guild.id)
        if not config or not config["enabled"]:
            continue

        member = guild.get_member(user.id)
        log_channel = bot.get_channel(config["log_channel_id"]) if config["log_channel_id"] else None

        if member and config["auto_ban"]:
            try:
                await guild.ban(member, reason=f"Global ban: {reason}")
                if log_channel:
                    await log_channel.send(f"✅ {user} was auto-banned due to a global ban.")
            except Exception as e:
                if log_channel:
                    await log_channel.send(f"⚠️ Failed to auto-ban {user}: {e}")
        elif log_channel:
            embed = discord.Embed(title="🚨 Global Ban Notice", description=f"User: {user.mention}\nReason: {reason}", color=0xff0000)
            for url in proof_urls:
                embed.set_image(url=url)
                await log_channel.send(embed=embed)

bot.run("YOUR_BOT_TOKEN")