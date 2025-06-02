from discord.ext import commands
import db


# Decorator function to check whether a user is a moderator
def is_moderator():
    def predicate(ctx):
        print(f"Checking moderator for: {ctx.author} - Has permission: {ctx.author.guild_permissions.manage_messages}")
        return ctx.author.guild_permissions.manage_messages
    return commands.check(predicate)


# Decorator function to block cogs if the server is not in the whitelisted table
def is_whitelisted():
    async def predicate(ctx):
        # ctx.guild is None if the command is used in a DM
        if ctx.guild is None:
            return False

        return db.is_guild_whitelisted(ctx.guild.id)

    return commands.check(predicate)


# Decorator function to block cogs from being used outside of designated channel.
# def check_channel():
#     async def predicate(ctx):
#         if ctx.guild.