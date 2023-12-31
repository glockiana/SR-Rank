import discord, time, re, datetime
from discord.ext import commands
from cache import Users, Bans

# // Bans cog
class BansCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
    
    # // Ban an user command
    @commands.command(name="ban", description='`=ban (@user) (length) (reason)  |  Lengths: [s (seconds), m (minutes), h (hours), d (days)]`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ban(self, ctx: commands.Context, user: discord.Member, length: str, *args):
        if ctx.author.bot:
            return
        
        # // Check if the user has enough permissions
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Get the ban length as an integer
        if "s" in length:
            length = int(re.sub("\D", "", length))
        elif "m" in length:
            length = int(re.sub("\D", "", length)) * 60
        elif "h" in length:
            length = int(re.sub("\D", "", length)) * 3600
        elif "d" in length:
            length = int(re.sub("\D", "", length)) * 86400
        else:
            length = 0
        
        # // Chekc if the user already exists in the bans table
        if Bans.is_banned(ctx.guild.id, user.id):
            # // Get the ban data
            ban_data: dict = Bans.get(ctx.guild.id, user.id)

            # // If the users ban time hasn't expired yet
            if ban_data.get("length", 0) - time.time() > 0:
                # // Get the ban length
                length: datetime.timedelta = datetime.timedelta(seconds = int(ban_data.get("length", 0) - time.time()))

                # // Send the embed
                return await ctx.send(
                    embed = discord.Embed(
                        title = f"{user.name} is already banned", 
                        description = f"**Length:** {length}\n**Reason:** {ban_data.get('reason', 'None')}\n**Banned by:** {ban_data.get('banned_by', 'Unknown')}", 
                        color = 15158588
                ))
            
            # // Else, Unban the user
            else:
                await Bans.unban(ctx.guild.id, user.id)
            
        # // Ban the user (time, reason)
        ban_time: int = int(length + time.time())
        ban_reason: str = ' '.join(word for word in args)
        
        # // Ban the user
        await Bans.ban(ctx.guild.id, user.id, ban_time, ban_reason, ctx.author.id)
        
        # // Send the embed
        length: int = datetime.timedelta(seconds = int(ban_time-time.time()))
        await ctx.send(
            embed = discord.Embed(
                title = f"{user.name} banned", 
                description = f"**Length:** {length}\n**Reason:** {ban_reason}\n**Banned by:** {ctx.author.mention}", 
                color = 15158588
        ))


    # // Unban an user command
    @commands.command(name="unban", description='`=unban (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def unban(self, ctx:commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the user has mod role
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // If the user exists in the bans cache and database
        if not Bans.is_banned(ctx.guild.id, user.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} is not banned", 
                    color = 33023
            ))
        
        # // Unban the user
        await Bans.unban(ctx.guild.id, user.id)
        
        # // Send the embed
        await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has unbanned {user.mention}", 
                color = 3066992
        ))

# // Setup the cog
async def setup(client: commands.Bot):
    await client.add_cog(BansCog(client))