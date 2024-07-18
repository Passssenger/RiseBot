import discord
from discord.ext import commands
import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='=', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Streaming(name="Rise", url="https://www.twitch.tv/rise"))

@bot.event
async def on_member_join(member):
    embed = discord.Embed(title="Welcome to Rise!", description="**Provide us a proof that you're a member of Rise**\n\n* How do I do that?\n* =submit <proof attachment>", color=0x00ff00)
    await member.send(embed=embed)

@bot.command()
async def submit(ctx, attachment: discord.Attachment = None):
    if ctx.guild:
        await ctx.send("Please use this command in a direct message.")
        return

    if not attachment:
        await ctx.send("Please provide an attachment with your submission.")
        return

    guild = bot.get_guild(1263508859054718986)  # Replace with your server's ID
    if not guild:
        await ctx.send("Error: Couldn't find the server. Please contact an administrator.")
        return

    role_id = 1263509430490759168
    role = guild.get_role(role_id)
    
    if role is None:
        await ctx.send("Error: Verification role not found. Please contact an administrator.")
        return

    member = guild.get_member(ctx.author.id)
    if not member:
        await ctx.send("Error: Couldn't find your member profile. Please make sure you're in the server.")
        return

    await member.add_roles(role)
    await ctx.send("**You have been verified!**")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member.name} has been banned. Reason: {reason}")
        await send_dm(member, "ban", reason, ctx.author)
    except discord.Forbidden:
        await ctx.send("I don't have permission to ban this user.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f"Unbanned {user.mention}")
            return
    await ctx.send(f"Couldn't find {member} in the ban list.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"{member.name} has been kicked. Reason: {reason}")
        await send_dm(member, "kick", reason, ctx.author)
    except discord.Forbidden:
        await ctx.send("I don't have permission to kick this user.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration: int):
    try:
        await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=duration))
        await ctx.send(f"{member.name} has been muted for {duration} minutes.")
        await send_dm(member, "mute", f"Duration: {duration} minutes", ctx.author)
    except discord.Forbidden:
        await ctx.send("I don't have permission to mute this user.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"{member.name} has been unmuted.")
        await send_dm(member, "unmute", "You have been unmuted", ctx.author)
    except discord.Forbidden:
        await ctx.send("I don't have permission to unmute this user.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"Cleared {amount} messages.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def snipe(ctx, ign: str, *, reason: str):
    embed = discord.Embed(title="Snipe Request Issued", color=0x00ff00)
    embed.add_field(name="Target IGN", value=ign, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Issued by", value=ctx.author.mention, inline=False)
    
    await ctx.send(embed=embed)

    channel = bot.get_channel(1263513026540077088)
    if channel:
        view = ConfirmView(ctx, ign, reason)
        await channel.send("New snipe request. Please review:", embed=embed, view=view)
    else:
        await ctx.send("Couldn't find the specified channel for review.")

class ConfirmView(discord.ui.View):
    def __init__(self, ctx, ign, reason):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.ign = ign
        self.reason = reason

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfirmModal(self.ctx, self.ign, self.reason, True))

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfirmModal(self.ctx, self.ign, self.reason, False))

class ConfirmModal(discord.ui.Modal, title="Confirm Action"):
    def __init__(self, ctx, ign, reason, accepted):
        super().__init__()
        self.ctx = ctx
        self.ign = ign
        self.reason = reason
        self.accepted = accepted

    confirmation = discord.ui.TextInput(label="Type the target's IGN to confirm")

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value.lower() == self.ign.lower():
            action = "accepted" if self.accepted else "denied"
            await interaction.response.send_message(f"Action {action} for IGN: {self.ign}.")
            
            embed = discord.Embed(title="GvG Notification", color=0xFF5733)
            embed.add_field(name="Action", value="Snipe request " + action, inline=False)
            embed.add_field(name="Target IGN", value=self.ign, inline=False)
            embed.add_field(name="Reason", value=self.reason, inline=False)
            embed.add_field(name="Issued by", value=self.ctx.author.mention, inline=False)
            
            notification_channel = self.ctx.guild.get_channel(1263513026540077088)
            if notification_channel:
                await notification_channel.send(embed=embed)
            else:
                await interaction.followup.send("Couldn't send notification to the designated channel.")
        else:
            await interaction.response.send_message("Confirmation failed. IGNs do not match.", ephemeral=True)

async def send_dm(member, action, reason, issuer):
    embed = discord.Embed(title=f"You have been {action}ed", color=0xFF0000)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Issued by", value=issuer.mention, inline=False)
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass  # Unable to send DM to the user

@ban.error
@unban.error
@kick.error
@mute.error
@unmute.error
@clear.error
@snipe.error
async def command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. Please check the command usage.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

bot.run('TOKEN')
