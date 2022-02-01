from discord_components import *
from discord.ext import commands
import discord, asyncio
from functools import *
from _sql import *

class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client
        # 1 == true, 0 == false
    
    # // RETURN CORRESPONDING EMOJI TO SETTING
    # /////////////////////////////////////////
    async def _guild_settings_status(self, option, row):
        # // MATCH CATEGORIES
        if option == "match_category":
            if row[2] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]

        # // MATCH LOGGING
        if option == "match_logging":
            if row[4] != 0: # false
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]

    # // RETURN CORRESPONDING EMOJI TO SETTING
    # /////////////////////////////////////////
    async def _lobby_settings_status(self, option, row):
        # // MAP PICKING PHASE
        if option == "map_pick_phase":
            if row[2] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]

        # // TEAM PICKING PHASE
        if option == "team_pick_phase":
            if row[3] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]
        
        # // NEGATIVE ELO
        if option == "negative_elo":
            if row[7] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]
        
        
    # // ADD MAP TO THE DATABASE
    # /////////////////////////////////////////
    async def _add_map(self, ctx, map, lobby):
        if not await SQL_CLASS().exists(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby} AND map = '{map}'"):
            await SQL_CLASS().execute(f"INSERT INTO maps (guild_id, lobby_id, map) VALUES ({ctx.guild.id}, {lobby}, '{map}')")
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} added **{map}** to the map pool", color=3066992))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} **{map}** already exists", color=15158588))

    # // REMOVE MAP FROM THE DATABASE
    # /////////////////////////////////////////
    async def _del_map(self, ctx, map, lobby):
        if await SQL_CLASS().exists(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby} AND map = '{map}'"):
            await SQL_CLASS().execute(f"DELETE FROM maps WHERE map = '{map}' AND guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} removed **{map}** from the map pool", color=3066992))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} **{map}** is not in the map pool", color=15158588))

    # // GUILD LOBBIES COMMAND
    # /////////////////////////////
    @commands.command(description="`=lobby add`**,** `=lobby delete`**,** `=lobby list`**,** `=lobby settings`")
    @commands.has_permissions(administrator=True)
    async def lobby(self, ctx, action:str):
        rows = await SQL_CLASS().select_all(f"SELECT lobby FROM lobbies WHERE guild_id = {ctx.guild.id}")
        # // CREATE A NEW LOBBY
        if action in ["add", "create"]:
            if len(rows) < 10:
                if not await SQL_CLASS().exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                    await SQL_CLASS().execute(f"INSERT INTO lobbies (guild_id, lobby) VALUES ({ctx.guild.id}, {ctx.channel.id})")
                    
                    if not await SQL_CLASS().exists(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}"):
                        await SQL_CLASS().execute(f"INSERT INTO lobby_settings (guild_id, lobby_id, map_pick_phase, team_pick_phase, win_elo, loss_elo, party_size, negative_elo, queue_size) VALUES ({ctx.guild.id}, {ctx.channel.id}, 0, 1, 5, 2, 1, 1, 10)")
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(rows)+1}/10]** {ctx.author.mention} has created a new lobby **{ctx.channel.name}**", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is already a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} maximum amount of lobbies created **[10/10]**", color=15158588))

        # // SHOW ALL GUILD LOBBIES
        if action in ["show", "list"]:
            if len(rows) > 0:
                embed=discord.Embed(title=f"Lobbies ┃ {ctx.guild.name}", color=33023)
                for i in range(len(rows)):
                    try:
                        embed.add_field(name= f"{i+1}. " + ctx.guild.get_channel(int(rows[i][0])).name, value=ctx.guild.get_channel(int(rows[i][0])).mention)
                    except Exception: pass
                return await ctx.send(embed=embed)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this server has no lobbies", color=15158588))

        # // DELETE AN EXISTING LOBBY
        if action in ["delete", "remove", "del"]:
            if await SQL_CLASS().exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                await SQL_CLASS().execute(f"DELETE FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                await SQL_CLASS().execute(f"DELETE FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}")
                return await ctx.send(embed=discord.Embed(description=f"**[{len(rows)-1}/10]** {ctx.author.mention} has removed the lobby **{ctx.channel.name}**", color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        if action in ["settings", "sets", "options", "opts", "setting"]:
            if not await SQL_CLASS().exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

            lobby_settings = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
            team_pick_phase = await self._lobby_settings_status("team_pick_phase", lobby_settings)
            map_pick_phase = await self._lobby_settings_status("map_pick_phase", lobby_settings)
            negative_elo = await self._lobby_settings_status("negative_elo", lobby_settings)
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} ┃ **Ten Man's {ctx.channel.mention} Settings Menu**", color=33023),
                components=[
                    Select(
                        placeholder="View Settings",
                        options=[
                            SelectOption(emoji=f'🔵', label="Add Map", value="add_map"),
                            SelectOption(emoji=f'🔵', label="Remove Map", value="remove_map"),
                            SelectOption(emoji=f'🔵', label="Change Queue Size", value="change_queue_size"),
                            SelectOption(emoji=f'🔵', label="Change Elo Per Win", value="change_win_elo"),
                            SelectOption(emoji=f'🔵', label="Change Elo Per Loss", value="change_loss_elo"),
                            SelectOption(emoji=f'🔵', label="Change Queue Party Size", value="change_queue_party_size"),
                            SelectOption(emoji=f'{negative_elo[0]}', label=f"{negative_elo[1]} Negative Elo", value="negative_elo"),
                            SelectOption(emoji=f'{map_pick_phase[0]}', label=f"{map_pick_phase[1]} Map Picking Phase", value="map_pick_phase"),
                            SelectOption(emoji=f'{team_pick_phase[0]}', label=f"{team_pick_phase[1]} Team Picking Phase", value="team_pick_phase")
                        ])])


    # // ADD MAP COMMAND
    # /////////////////////////////////////////
    @commands.command(description="`=addmap (map name)`")
    @commands.has_permissions(administrator=True)
    async def addmap(self, ctx, map:str):
        if not ctx.author.bot:
            if await SQL_CLASS().exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                return await self._add_map(ctx, map, ctx.channel.id)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // DELETE MAP COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["removemap", "deletemap"], description="`=delmap (map name)`")
    @commands.has_permissions(administrator=True)
    async def delmap(self, ctx, map:str):
        if not ctx.author.bot:
            if await SQL_CLASS().exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                return await self._del_map(ctx, map, ctx.channel.id)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // SHOW LIST OF MAPS COMMAND
    # /////////////////////////////////////////
    @commands.command(description="`=maps`")
    async def maps(self, ctx):
        if not ctx.author.bot:
            if await SQL_CLASS().exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                rows = await SQL_CLASS().select_all(f"SELECT map FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                return await ctx.send(embed=discord.Embed(title=f"Maps ┃ {ctx.guild.name}", description="\n".join(e[0] for e in rows), color=33023))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // SET THE REGISTER ROLE COMMAND
    # /////////////////////////////////////////
    @commands.command(description="`=regrole (@role)`")
    @commands.has_permissions(administrator=True)
    async def regrole(self, ctx, role:discord.Role):
        if not ctx.author.bot:
            if await SQL_CLASS().exists(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}"):
                await SQL_CLASS().execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {ctx.guild.id}")
                return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} set the register role to {role.mention}', color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} the owner has not setup the bot yet", color=15158588))

    # // SHOW SETTINGS MENU COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["sets", "options"], description="`=settings`")
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        if not ctx.author.bot:
            if not await SQL_CLASS().exists(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}"):
               await SQL_CLASS().execute(f"INSERT INTO settings (guild_id, reg_role, match_categories, reg_channel, match_logs) VALUES ({ctx.guild.id}, 0, 0, 0, 0)")

            settings = await SQL_CLASS().select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            match_category = await self._guild_settings_status("match_category", settings)
            match_logging = await self._guild_settings_status("match_logging", settings)

            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} ┃ **Ten Man's Server Settings Menu**", color=33023),
                components=[
                    Select(
                        placeholder="View Settings",
                        options=[
                            SelectOption(emoji=f'🔵', label="Create Queue Embed", value="queue_embed"),
                            SelectOption(emoji=f'🔵', label="Change Register Role", value="change_reg_role"),
                            SelectOption(emoji=f'🔵', label="Change Register Channel", value="change_reg_channel"),
                            SelectOption(emoji=f'{match_logging[0]}', label=f"{match_logging[1]} Match Logging", value="match_logging"),
                            SelectOption(emoji=f'{match_category[0]}', label=f"{match_category[1]} Match Categories", value="match_category")
                        ])])

    # // SELECT MENU LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_select_option(self, res):
        if not res.author.bot:
            try:
                # // CHANGE QUEUE SIZE
                if res.values[0] == "change_queue_size":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the queue size **(4-20)**", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        
                        if int(c.content) >= 4 and int(c.content) <= 20:
                            await SQL_CLASS().execute(f"UPDATE lobby_settings SET queue_size = {int(c.content)} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has set the queue size to **{c.content} players**", color=3066992))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} please respond with a number from **4-20**", color=15158588))
                
                # // MAP PICKING PHASE
                if res.values[0] == 'map_pick_phase':
                    if res.author.guild_permissions.administrator:
                        row = (await SQL_CLASS().select(f"SELECT map_pick_phase FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}"))[0]
                        if row == 0:
                            await SQL_CLASS().execute(f"UPDATE lobby_settings SET map_pick_phase = 1 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Map Picking Phase**", color=3066992))

                        await SQL_CLASS().execute(f"UPDATE lobby_settings SET map_pick_phase = 0 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Map Picking Phase**", color=3066992))

                # // MATCH LOGGING
                if res.values[0] == "match_logging":
                    if res.author.guild_permissions.administrator:
                        row = (await SQL_CLASS().select(f"SELECT match_logs FROM settings WHERE guild_id = {res.guild.id}"))[0]
                        if row == 0:
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the channel you want to use", color=33023))
                            c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                            if "#" in c.content:
                                channel = res.guild.get_channel(int(str(c.content).strip("<").strip(">").strip("#")))
                                await SQL_CLASS().execute(f"UPDATE settings SET match_logs = {channel.id} WHERE guild_id = {res.guild.id}")
                                return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Match Logging** in **{channel.mention}**", color=3066992))
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} invalid channel (please mention the channel)", color=15158588))

                        await SQL_CLASS().execute(f"UPDATE settings SET match_logs = 0 WHERE guild_id = {res.guild.id}")
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Match Logging**", color=3066992))

                # // MATCH CATEGORIES
                if res.values[0] == 'match_category':
                    if res.author.guild_permissions.administrator:
                        row = (await SQL_CLASS().select(f"SELECT match_categories FROM settings WHERE guild_id = {res.guild.id}"))[0]
                        if row == 0:
                            await SQL_CLASS().execute(f"UPDATE settings SET match_categories = 1 WHERE guild_id = {res.guild.id}")
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Match Categories**", color=3066992))

                        await SQL_CLASS().execute(f"UPDATE settings SET match_categories = 0 WHERE guild_id = {res.guild.id}")
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Match Categories**", color=3066992))

                # // TEAM PICKING PHASE
                if res.values[0] == 'team_pick_phase':
                    if res.author.guild_permissions.administrator:
                        row = (await SQL_CLASS().select(f"SELECT team_pick_phase FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}"))[0]
                        if row == 0:
                            await SQL_CLASS().execute(f"UPDATE lobby_settings SET team_pick_phase = 1 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Team Picking Phase**", color=3066992))

                        await SQL_CLASS().execute(f"UPDATE lobby_settings SET team_pick_phase = 0 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Team Picking Phase**", color=3066992))

                # // CHANGE THE REGISTER ROLE
                if res.values[0] == "change_reg_role":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the role you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        if "@" in str(c.content):
                            role = res.guild.get_role(int(str(c.content).strip("<").strip(">").strip("@").strip("&")))
                            await SQL_CLASS().execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {res.guild.id}")
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Role** to {role.mention}", color=3066992))
                        
                        await SQL_CLASS().execute(f"UPDATE settings SET reg_role = 0 WHERE guild_id = {res.guild.id}")
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Role** to **None**", color=3066992))

                # // ADD MAP
                if res.values[0] == "add_map":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        await self._add_map(res, c.content, res.channel.id)

                # // REMOVE MAP
                if res.values[0] == "remove_map":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        await self._del_map(res, c.content, res.channel.id)
                
                # // NEGATIVE ELO
                if res.values[0] == "negative_elo":
                    if res.author.guild_permissions.administrator:
                        row = (await SQL_CLASS().select(f"SELECT negative_elo FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}"))[0]
                        if row == 0:
                            await SQL_CLASS().execute(f"UPDATE lobby_settings SET negative_elo = 1 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Negative Elo**", color=3066992))

                        await SQL_CLASS().execute(f"UPDATE lobby_settings SET negative_elo = 0 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} Success!", color=3066992))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Negative Elo**", color=3066992))

                # // CHANGE THE REGISTER CHANNEL
                if res.values[0] == "change_reg_channel":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the channel you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        if "<#" not in str(c.content):
                            await SQL_CLASS().execute(f"UPDATE settings SET reg_channel = 0 WHERE guild_id = {res.guild.id}")
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Channel** to **None**", color=3066992))

                        channel = res.guild.get_channel(int(str(c.content).strip("<").strip(">").strip("#")))
                        await SQL_CLASS().execute(f"UPDATE settings SET reg_channel = {channel.id} WHERE guild_id = {res.guild.id}")
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Channel** to {channel.mention}", color=3066992))
                
                # // CHANGE THE ELO PER WIN
                if res.values[0] == "change_win_elo":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the amount of elo you want to gain", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        await SQL_CLASS().execute(f"UPDATE lobby_settings SET win_elo = {int(c.content)} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has set the **Win Elo** to **{c.content}**", color=3066992))
                    
                # // CHANGE THE ELO PER LOSS
                if res.values[0] == "change_loss_elo":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the amount of elo you want to lose", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        await SQL_CLASS().execute(f"UPDATE lobby_settings SET loss_elo = {int(c.content)} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has set the **Loss Elo** to **{c.content}**", color=3066992))

                # // QUEUE EMBED
                if res.values[0] == "queue_embed":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond which lobby you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        
                        channel = res.guild.get_channel(int(str(c.content).strip("<").strip(">").strip("#")))
                        if await SQL_CLASS().exists(f"SELECT * FROM lobbies WHERE guild_id = {res.guild.id} AND lobby = {channel.id}"):
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} has created a new **Queue Embed**", color=3066992))
                            embed=discord.Embed(title=f'[0/10] {channel.name}', color=33023)
                            embed.set_footer(text=str(channel.id))

                            return await res.channel.send(embed=embed, components=[[
                                Button(style=ButtonStyle.green, label='Join', custom_id='join_queue'),
                                Button(style=ButtonStyle.red, label="Leave", custom_id='leave_queue')]])
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} that channel is not a lobby", color=15158588))
                                

                if res.values[0] == "change_queue_party_size":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the maximum party size", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        await SQL_CLASS().execute(f"UPDATE lobby_settings SET party_size = {int(c.content)} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has set the **Maximum Party Size** to **{c.content}**", color=3066992))
            except asyncio.TimeoutError:
                return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} you did not respond in time", color=15158588))
                
def setup(client):
    client.add_cog(Settings(client))