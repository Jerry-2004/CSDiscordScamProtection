from discord.ext import commands
import discord

from decorators import is_whitelisted

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Help cog initialized.")


    @commands.command(name='help')
    @is_whitelisted()
    async def help_command(self, ctx):
        try:
            embed = discord.Embed(
                title="📘 Scam Protection Bot Help",
                description="Here are the available commands:",
                color=discord.Color.blue()
            )
            embed.add_field(name="🔨 ;ban {user_id}",
                            value="Starts a ban process with a reason and evidence. **Mods only.**", inline=False)
            embed.add_field(name="♻️ ;unban {user_id}",
                            value="Initiates a vote to unban a user. Needs 10 approvals or owner override. **Mods only.**",
                            inline=False)
            embed.add_field(name="🌐 ;servers",
                            value="Lists all whitelisted servers where the bot is active. **Mods only.**", inline=False)
            embed.add_field(name="📄 ;help", value="Shows this message.", inline=False)
            embed.set_footer(text="Use commands responsibly. Bot only works in whitelisted servers.")

            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            await ctx.send(embed=embed)
            print("Embed sent successfully.")
        except Exception as e:
            print(f"Error sending embed: {e}")


async def setup(bot):
    await bot.add_cog(Help(bot))
