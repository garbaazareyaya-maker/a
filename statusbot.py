import discord
from discord.ext import commands
import json
import os
import datetime

def load_config():
    if not os.path.exists('config.json'):
        return {}
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config_data):
    with open('config.json', 'w') as f:
        json.dump(config_data, f, indent=2)

config = load_config()
STATUS_TOKEN = config.get('status_token')
COMMAND_PREFIX = '$'
STATUS_MUST_BE = config.get('status_must_be')
STATUS_ROLE_ID = config.get('status_role_id')
STATUS_LOG_CHANNEL_ID = config.get('status_log_channel_id')

USER_ROLES_FILE = 'user_status_roles.json'

def load_user_roles():
    if not os.path.exists(USER_ROLES_FILE):
        return {}
    with open(USER_ROLES_FILE, 'r') as f:
        data = json.load(f)
        return {int(k): v for k, v in data.items()}

def save_user_roles(user_roles_data):
    with open(USER_ROLES_FILE, 'w') as f:
        data = {str(k): v for k, v in user_roles_data.items()}
        json.dump(data, f, indent=2)

user_status_roles = load_user_roles()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

async def log_status_event(guild, event_type, user, role_name=None, reason=None):
    if not STATUS_LOG_CHANNEL_ID:
        return

    log_channel = guild.get_channel(STATUS_LOG_CHANNEL_ID)
    if not log_channel:
        return

    embed = discord.Embed(
        title=f"Status Bot Log - {event_type}",
        color=0xFFFFFF,
        timestamp=datetime.datetime.utcnow()
    )

    embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=True)
    if role_name:
        embed.add_field(name="Role", value=role_name, inline=True)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)

    embed.set_footer(text="Wither Cloud Status Manager")

    try:
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f"Failed to send log: {e}")

def check_user_status(member):
    if not member.activities or not STATUS_MUST_BE:
        return False

    for activity in member.activities:
        if hasattr(activity, 'name') and activity.name:
            if STATUS_MUST_BE.lower() in activity.name.lower():
                return True
    return False

@bot.event
async def on_ready():
    print(f'Status bot logged in as {bot.user.name} ({bot.user.id})')

@bot.event
async def on_presence_update(before, after):
    if before.bot or not STATUS_ROLE_ID or not STATUS_MUST_BE:
        return

    guild = after.guild
    role = guild.get_role(STATUS_ROLE_ID)
    if not role:
        return

    user_id = after.id

    if before.status != discord.Status.offline and after.status == discord.Status.offline:
        if role in after.roles:
            user_status_roles[user_id] = True
            save_user_roles(user_status_roles)
            try:
                await after.remove_roles(role)
                await log_status_event(guild, "Role Removed", after, role.name, "User went offline")
            except Exception as e:
                print(f"Failed to remove role from {after.display_name}: {e}")

    elif before.status == discord.Status.offline and after.status != discord.Status.offline:
        if user_id in user_status_roles and user_status_roles[user_id]:
            if check_user_status(after):
                if role not in after.roles:
                    try:
                        await after.add_roles(role)
                        await log_status_event(guild, "Role Restored", after, role.name, "User came back online with valid status")
                    except Exception as e:
                        print(f"Failed to restore role to {after.display_name}: {e}")
            else:
                user_status_roles[user_id] = False
                save_user_roles(user_status_roles)
                await log_status_event(guild, "Role Not Restored", after, role.name, "User came back online but status no longer matches")

    elif after.status != discord.Status.offline:
        has_valid_status = check_user_status(after)

        if has_valid_status and role not in after.roles:
            if user_id not in user_status_roles or not user_status_roles[user_id]:
                try:
                    await after.add_roles(role)
                    user_status_roles[user_id] = True
                    save_user_roles(user_status_roles)
                    await log_status_event(guild, "Role Given", after, role.name, "Status automatically detected")
                except Exception as e:
                    print(f"Failed to give role to {after.display_name}: {e}")

        elif not has_valid_status and role in after.roles:
            try:
                await after.remove_roles(role)
                user_status_roles[user_id] = False
                save_user_roles(user_status_roles)
                await log_status_event(guild, "Role Removed", after, role.name, "Status no longer matches requirement")
            except Exception as e:
                print(f"Failed to remove role from {after.display_name}: {e}")

@bot.command(name='send-gen-access')
async def send_gen_access(ctx, channel: discord.TextChannel = None):
    if not ctx.author.guild_permissions.manage_guild:
        await ctx.send("❌ You need **Manage Server** permissions to use this command.", delete_after=5)
        return

    if not channel:
        channel = ctx.channel

    if not STATUS_MUST_BE:
        await ctx.send("❌ Status requirement not configured in config.json", delete_after=5)
        return

    embed = discord.Embed(
        title="How to get Free Gen Access",
        color=0xFFFFFF,
        timestamp=datetime.datetime.utcnow()
    )

    embed.add_field(
        name="Step 1: Set Your Custom Status",
        value=f"Set your custom status as: `{STATUS_MUST_BE}`",
        inline=False
    )

    embed.add_field(
        name="Step 2: Run the Command",
        value="Go into <#1400551038297178233> and run `$cstatus`",
        inline=False
    )

    embed.add_field(
        name="Step 3: Wait for Verification",
        value="Give the bot a few seconds to verify your status and give you the role, then boom you have free gen access!",
        inline=False
    )

    embed.set_footer(text="Wither Cloud Status Manager")

    try:
        await channel.send(embed=embed)
        if channel != ctx.channel:
            await ctx.send(f"✅ Gen access instructions sent to {channel.mention}", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Failed to send message: {e}", delete_after=5)

@bot.command(name='cstatus')
async def check_status(ctx):
    if not STATUS_MUST_BE or not STATUS_ROLE_ID:
        embed = discord.Embed(
            title="❌ Configuration Error",
            description="Status checking is not properly configured.",
            color=0xFFFFFF,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Wither Cloud Status Manager")
        await ctx.send(embed=embed)
        return

    member = ctx.author
    if not member.activities:
        embed = discord.Embed(
            title="❌ No Status Found",
            description="You don't have any status set.",
            color=0xFFFFFF,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(
            name="Your status must be:",
            value=f"```{STATUS_MUST_BE}```",
            inline=False
        )
        embed.set_footer(text="Wither Cloud Status Manager")
        await ctx.send(embed=embed)
        await log_status_event(ctx.guild, "Manual Check Failed", member, None, "No status set")
        return

    for activity in member.activities:
        if hasattr(activity, 'name') and activity.name:
            if STATUS_MUST_BE.lower() in activity.name.lower():
                role = ctx.guild.get_role(STATUS_ROLE_ID)
                if role:
                    if role not in member.roles:
                        await member.add_roles(role)
                        user_status_roles[member.id] = True
                        save_user_roles(user_status_roles)

                        embed = discord.Embed(
                            title="✅ Role Assigned",
                            description=f"Role **{role.name}** has been given to you!",
                            color=0xFFFFFF,
                            timestamp=datetime.datetime.utcnow()
                        )
                        embed.set_footer(text="Wither Cloud Status Manager")
                        await ctx.send(embed=embed)
                        await log_status_event(ctx.guild, "Manual Check Success", member, role.name, f"Role given via $cstatus command")
                    else:
                        embed = discord.Embed(
                            title="ℹ️ Already Have Role",
                            description=f"You already have the **{role.name}** role!",
                            color=0xFFFFFF,
                            timestamp=datetime.datetime.utcnow()
                        )
                        embed.set_footer(text="Wither Cloud Status Manager")
                        await ctx.send(embed=embed)
                        await log_status_event(ctx.guild, "Manual Check", member, role.name, "User already has role")
                else:
                    embed = discord.Embed(
                        title="❌ Role Not Found",
                        description="Configured role not found.",
                        color=0xFFFFFF,
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.set_footer(text="Wither Cloud Status Manager")
                    await ctx.send(embed=embed)
                    await log_status_event(ctx.guild, "Manual Check Failed", member, None, "Configured role not found")
                return

    embed = discord.Embed(
        title="❌ Status Mismatch",
        description=f"Your status doesn't match the required text: `{STATUS_MUST_BE}`",
        color=0xFFFFFF,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="Wither Cloud Status Manager")
    await ctx.send(embed=embed)
    await log_status_event(ctx.guild, "Manual Check Failed", member, None, f"Status doesn't match: {STATUS_MUST_BE}")

if __name__ == "__main__":
    if not STATUS_TOKEN:
        print("Error: status_token not found in config.json")
        exit(1)

    try:
        bot.run(STATUS_TOKEN)
    except discord.LoginFailure:
        print("Error: Invalid status token")
    except Exception as e:
        print(f"Error starting status bot: {e}")