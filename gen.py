# Discord Bot for Account Generation
import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime
import asyncio
import traceback
import zoneinfo
import aiohttp
from typing import Optional
import io

# --- File and Directory Setup Function ---
def setup_bot_files():
    """
    Creates necessary files and directories for the bot to run.
    This function is called once on startup.
    """
    print("Starting bot file and directory setup...")

    # Define paths
    config_file = 'config.json'
    vouch_data_file = 'vouch_data.json'
    bot_admins_file = 'bot_admins.json'
    status_data_file = 'status_data.json'
    gen_bans_file = 'gen_bans.json'
    stock_base_dir = 'stock'
    stock_free_dir = os.path.join(stock_base_dir, 'free')
    stock_premium_dir = os.path.join(stock_base_dir, 'premium')
    stock_booster_dir = os.path.join(stock_base_dir, 'booster')

    # 1. Create config.json
    if not os.path.exists(config_file):
        initial_config = {
            "bot_token": "YOUR_BOT_TOKEN_HERE",
            "status_bot_token": "YOUR_STATUS_BOT_TOKEN_HERE",
            "command_prefix": "$",
            "allowed_guild_ids": [],
            "free_channel_ids": [],
            "premium_channel_ids": [],
            "booster_channel_ids": [],
            "restock_channel_id": None,
            "restock_role_id": None,
            "vouch_channel_id": None,
            "log_channel_id": None,
            "restock_logs_channel_id": None,
            "ban_logs_channel_id": None,
            "status_log_channel_id": None,
            "restocker_logs_id": None,
            "status_must_be": ".gg/withercloud",
            "status_role_id": None,
            "vouch_grace_period_seconds": 120,
            "free_gen_cooldown_seconds": 600,
            "premium_gen_cooldown_seconds": 3600,
            "booster_gen_cooldown_seconds": 1800,
            "bot_status": {"type": "playing", "name": ".gg/withercloud | $info"},
            "embed_color": "#ffffff",
            "embed_footer_text": "Wither Cloud",
            "embed_thumbnail_url": "https://cdn.discordapp.com/attachments/1404564902030610473/1421476187049431090/IMG_4683.png?ex=68d92c5c&is=68d7dadc&hm=a89e14d53156975b29446d41ed8fbaccddaf50672370424284c663135ba19351&"
        }
        with open(config_file, 'w') as f:
            json.dump(initial_config, f, indent=2)
        print(f"Created '{config_file}'. **IMPORTANT: Please replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token.**")
    else:
        print(f"'{config_file}' already exists. Skipping creation.")

    # 2. Create vouch_data.json
    if not os.path.exists(vouch_data_file):
        initial_vouch_data = {"total_vouches": 0}
        with open(vouch_data_file, 'w') as f:
            json.dump(initial_vouch_data, f, indent=2)
        print(f"Created '{vouch_data_file}'.")
    else:
        print(f"'{vouch_data_file}' already exists. Skipping creation.")

    # 3. Create bot_admins.json
    if not os.path.exists(bot_admins_file):
        initial_bot_admins = {"admin_ids": []}
        with open(bot_admins_file, 'w') as f:
            json.dump(initial_bot_admins, f, indent=2)
        print(f"Created '{bot_admins_file}'. **Remember to manually add your Discord User ID to this file to become an initial bot admin.**")
    else:
        print(f"'{bot_admins_file}' already exists. Skipping creation.")

    # 4. Create status_data.json
    if not os.path.exists(status_data_file):
        initial_status_data = {"status_role_assignments": {}}
        with open(status_data_file, 'w') as f:
            json.dump(initial_status_data, f, indent=2)
        print(f"Created '{status_data_file}'.")
    else:
        print(f"'{status_data_file}' already exists. Skipping creation.")

    # 5. Create gen_bans.json
    if not os.path.exists(gen_bans_file):
        initial_gen_bans = {}
        with open(gen_bans_file, 'w') as f:
            json.dump(initial_gen_bans, f, indent=2)
        print(f"Created '{gen_bans_file}'.")
    else:
        print(f"'{gen_bans_file}' already exists. Skipping creation.")

    # 6. Create stock directories
    os.makedirs(stock_free_dir, exist_ok=True)
    os.makedirs(stock_premium_dir, exist_ok=True)
    os.makedirs(stock_booster_dir, exist_ok=True)
    print(f"Ensured '{stock_free_dir}', '{stock_premium_dir}', and '{stock_booster_dir}' directories exist.")
    print("You can now place your account files (e.g., `netflix.txt`) inside these directories.")

    print("\nInitial file setup complete!")

# --- Configuration Loading ---
CONFIG_FILE = 'config.json'

def load_config():
    """Loads bot configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please ensure it is created by setup_bot_files.")
        return {}

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(new_config: dict):
    """Saves the current bot configuration to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(new_config, f, indent=2)
    print(f"Config updated and saved to {CONFIG_FILE}.")

# --- Gen Bans Management ---
GEN_BANS_FILE = 'gen_bans.json'

def load_gen_bans():
    """Load generation bans from file."""
    if os.path.exists(GEN_BANS_FILE):
        with open(GEN_BANS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_gen_bans(bans_data):
    """Save generation bans to file."""
    with open(GEN_BANS_FILE, 'w') as f:
        json.dump(bans_data, f, indent=2)

def add_gen_ban(user_id: int, moderator_id: int, reason: str, length_seconds: int = None):
    """Add a generation ban."""
    bans = load_gen_bans()
    end_ts = None
    if length_seconds:
        end_ts = int((datetime.datetime.utcnow() + datetime.timedelta(seconds=length_seconds)).timestamp())

    bans[str(user_id)] = {
        "moderator": moderator_id,
        "reason": reason,
        "end_ts": end_ts,
        "created_ts": int(datetime.datetime.utcnow().timestamp())
    }
    save_gen_bans(bans)

def remove_gen_ban(user_id: int):
    """Remove a generation ban."""
    bans = load_gen_bans()
    if str(user_id) in bans:
        del bans[str(user_id)]
        save_gen_bans(bans)

def is_gen_banned(user_id: int):
    """Check if user is generation banned."""
    bans = load_gen_bans()
    data = bans.get(str(user_id))
    if not data:
        return False, None

    end_ts = data.get("end_ts")
    if end_ts and int(datetime.datetime.utcnow().timestamp()) > end_ts:
        # Ban expired; remove
        remove_gen_ban(user_id)
        return False, None

    return True, data

# --- Vouch Data Persistence ---
VOUCH_DATA_FILE = 'vouch_data.json'
vouch_count = 0

def load_vouch_data():
    global vouch_count
    if os.path.exists(VOUCH_DATA_FILE):
        with open(VOUCH_DATA_FILE, 'r') as f:
            data = json.load(f)
            vouch_count = data.get('total_vouches', 0)
    else:
        print(f"Warning: {VOUCH_DATA_FILE} not found. Running setup_bot_files() should create it.")
        save_vouch_data()

def save_vouch_data():
    with open(VOUCH_DATA_FILE, 'w') as f:
        json.dump({'total_vouches': vouch_count}, f, indent=2)

# --- Bot Admin Persistence ---
BOT_ADMINS_FILE = 'bot_admins.json'
bot_admin_ids = set()

def load_bot_admins():
    global bot_admin_ids
    if os.path.exists(BOT_ADMINS_FILE):
        with open(BOT_ADMINS_FILE, 'r') as f:
            data = json.load(f)
            bot_admin_ids = set(data.get('admin_ids', []))
    else:
        print(f"Warning: {BOT_ADMINS_FILE} not found. Running setup_bot_files() should create it.")
        save_bot_admins()

def save_bot_admins():
    with open(BOT_ADMINS_FILE, 'w') as f:
        json.dump({'admin_ids': list(bot_admin_ids)}, f, indent=2)

# --- Status Data Persistence ---
STATUS_DATA_FILE = 'status_data.json'
status_role_assignments = {}

def load_status_data():
    global status_role_assignments
    if os.path.exists(STATUS_DATA_FILE):
        with open(STATUS_DATA_FILE, 'r') as f:
            data = json.load(f)
            status_role_assignments = {int(k): v for k, v in data.get('status_role_assignments', {}).items()}
    else:
        print(f"Warning: {STATUS_DATA_FILE} not found. Creating it.")
        save_status_data()

def save_status_data():
    with open(STATUS_DATA_FILE, 'w') as f:
        data = {'status_role_assignments': {str(k): v for k, v in status_role_assignments.items()}}
        json.dump(data, f, indent=2)

# --- Setup and Load Configuration BEFORE Defining Variables ---
setup_bot_files()

config = load_config()
load_vouch_data()
load_bot_admins()
load_status_data()

# Define global configuration variables from loaded config
BOT_TOKEN = config.get('bot_token')
STATUS_BOT_TOKEN = config.get('status_bot_token')
COMMAND_PREFIX = config.get('command_prefix', '$')
ALLOWED_GUILD_IDS = config.get('allowed_guild_ids', [])
FREE_CHANNEL_IDS = config.get('free_channel_ids', [])
PREMIUM_CHANNEL_IDS = config.get('premium_channel_ids', [])
BOOSTER_CHANNEL_IDS = config.get('booster_channel_ids', [])
RESTOCK_CHANNEL_ID = config.get('restock_channel_id')
RESTOCK_ROLE_ID = config.get('restock_role_id')
VOUCH_CHANNEL_ID = config.get('vouch_channel_id')
LOG_CHANNEL_ID = config.get('log_channel_id')
RESTOCK_LOGS_CHANNEL_ID = config.get('restock_logs_channel_id')
BAN_LOGS_CHANNEL_ID = config.get('ban_logs_channel_id')
STATUS_LOG_CHANNEL_ID = config.get('status_log_channel_id')
RESTOCKER_LOGS_ID = config.get('restocker_logs_id')
STATUS_MUST_BE = config.get('status_must_be', '.gg/withercloud')
STATUS_ROLE_ID = config.get('status_role_id')
VOUCH_GRACE_PERIOD_SECONDS = config.get('vouch_grace_period_seconds', 120)
FREE_GEN_COOLDOWN_SECONDS = config.get('free_gen_cooldown_seconds', 600)
PREMIUM_GEN_COOLDOWN_SECONDS = config.get('premium_gen_cooldown_seconds', 3600)
BOOSTER_GEN_COOLDOWN_SECONDS = config.get('booster_gen_cooldown_seconds', 1800)
BOT_STATUS_CONFIG = config.get('bot_status', {"type": "playing", "name": ".gg/withercloud | $info"})
EMBED_COLOR_HEX = config.get('embed_color', '#ffffff')
BOT_FOOTER_TEXT_BASE = config.get('embed_footer_text', 'Wither Cloud')
EMBED_THUMBNAIL_URL = config.get('embed_thumbnail_url', '')

# --- Helper: Convert hex color to discord.Color ---
def hex_to_discord_color(hex_string: str) -> discord.Color:
    """Converts a hex color string (#FFFFFF) to discord.Color."""
    hex_string = hex_string.lstrip('#')
    return discord.Color(int(hex_string, 16))

EMBED_COLOR = hex_to_discord_color(EMBED_COLOR_HEX)

# --- Timezone Setup ---
try:
    EST_TIMEZONE = zoneinfo.ZoneInfo("America/New_York")
except Exception:
    EST_TIMEZONE = datetime.timezone.utc
    print("Warning: Could not load EST timezone. Using UTC instead.")

BOT_AUTHOR_NAME = BOT_FOOTER_TEXT_BASE
EMBED_FOOTER_TEXT = f"{BOT_FOOTER_TEXT_BASE} • {datetime.datetime.now(EST_TIMEZONE).strftime('%m/%d/%Y')}"

# --- Bot Initialization ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    help_command=None
)

# Vouch timer tracking
vouch_timers = {}

# --- Enhanced Embed Creation ---
def create_enhanced_embed(
    title: str = None,
    description: str = None,
    color: discord.Color = None,
    ctx_or_interaction = None,
    embed_style: str = "default"
) -> discord.Embed:
    """
    Creates a standardized, enhanced embed with consistent styling.
    """
    if color is None:
        if embed_style == "success":
            color = discord.Color.green()
        elif embed_style == "error":
            color = discord.Color.red()
        elif embed_style == "warning":
            color = discord.Color.orange()
        elif embed_style == "info":
            color = discord.Color.blue()
        elif embed_style == "admin":
            color = discord.Color.gold()
        elif embed_style == "vouch":
            color = discord.Color.purple()
        else:
            color = EMBED_COLOR

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.now(EST_TIMEZONE)
    )

    embed.set_author(name=BOT_AUTHOR_NAME, icon_url=EMBED_THUMBNAIL_URL)
    if EMBED_THUMBNAIL_URL:
        embed.set_thumbnail(url=EMBED_THUMBNAIL_URL)
    embed.set_footer(text=EMBED_FOOTER_TEXT, icon_url=EMBED_THUMBNAIL_URL)

    return embed

# --- Helper Function for Duration Parsing ---
def parse_duration(duration_str: str) -> datetime.timedelta:
    """
    Parses a duration string (e.g., "5m", "1h", "3d", "3w", "3mo") into a timedelta object.
    """
    unit_map = {
        'm': 'minutes',
        'h': 'hours',
        'd': 'days',
        'w': 'weeks',
        'mo': 'months'
    }

    if not duration_str or len(duration_str) < 2:
        raise ValueError("Invalid duration format. Use like '5m', '1h', '3d'.")

    value = int(duration_str[:-1])
    unit = duration_str[-1].lower()

    if unit == 'o' and duration_str[-2].lower() == 'm':
        unit = 'mo'
    elif unit not in unit_map:
        raise ValueError("Invalid duration unit. Use 'm', 'h', 'd', 'w', 'mo'.")

    if unit == 'mo':
        return datetime.timedelta(days=value * 30)
    else:
        return datetime.timedelta(**{unit_map[unit]: value})

# --- Stock Management Functions ---
STOCK_BASE_DIR = "stock"

def get_stock_file_path(service_type: str, service_name: str) -> str:
    """Constructs the file path for a given service stock."""
    return os.path.join(STOCK_BASE_DIR, service_type, f"{service_name.lower().replace(' ', '_')}.txt")

def read_accounts_from_file(file_path: str) -> list[str]:
    """Reads all account lines from a given file path."""
    accounts = []
    try:
        with open(file_path, 'r') as f:
            accounts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error reading accounts from '{file_path}': {e}.")
    return accounts

def write_accounts_to_file(file_path: str, accounts: list[str]):
    """Writes a list of account lines to a given file path."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            for account in accounts:
                f.write(f"{account}\n")
    except Exception as e:
        print(f"Error writing accounts to '{file_path}': {e}")

def read_all_stock_data() -> dict:
    """
    Reads stock counts from all .txt files within 'stock/free', 'stock/premium', and 'stock/booster' directories.
    """
    stock_data = {"free": {}, "premium": {}, "booster": {}}
    total_stock = 0

    for category in ["free", "premium", "booster"]:
        category_path = os.path.join(STOCK_BASE_DIR, category)
        if not os.path.exists(category_path):
            print(f"Warning: Stock category directory '{category_path}' not found. Skipping.")
            continue

        for filename in os.listdir(category_path):
            if filename.endswith(".txt"):
                service_name = os.path.splitext(filename)[0].replace("_", " ").upper()
                file_path = os.path.join(category_path, filename)
                accounts = read_accounts_from_file(file_path)
                count = len(accounts)

                stock_data[category][service_name] = count
                total_stock += count

    stock_data['total_stock'] = total_stock
    return stock_data

# --- Logging Function ---
async def log_event(event_type: str, description: str, color: discord.Color, fields: list = None, author: discord.Member = None, target: discord.Member = None, channel: discord.TextChannel = None, ctx_or_interaction=None):
    """
    Sends a structured embed to the configured log channel.
    """
    log_channel_obj = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel_obj:
        print(f"Error: Log channel with ID {LOG_CHANNEL_ID} not found or not configured.")
        return

    embed = create_enhanced_embed(
        title=f"🔍 {event_type}",
        description=description,
        color=color,
        ctx_or_interaction=ctx_or_interaction
    )

    if author:
        embed.add_field(name="👤 Initiator", value=f"{author.mention} ({author.id})", inline=True)
    if target:
        embed.add_field(name="🎯 Target", value=f"{target.mention} ({target.id})", inline=True)
    if channel:
        embed.add_field(name="📍 Channel", value=f"{channel.mention} ({channel.id})", inline=True)

    if fields:
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))

    try:
        await log_channel_obj.send(embed=embed)
    except Exception as e:
        print(f"Error sending log message: {e}")

# --- Ban Logging Function ---
async def log_ban_event(guild: discord.Guild, user: discord.User, moderator: discord.User, reason: str, duration_seconds: int = None, ban_type: str = "Generation"):
    """Log ban events to the ban logs channel."""
    if not BAN_LOGS_CHANNEL_ID:
        return

    ban_logs_channel = guild.get_channel(BAN_LOGS_CHANNEL_ID)
    if not ban_logs_channel:
        return

    duration_text = "Permanent" if not duration_seconds else str(datetime.timedelta(seconds=duration_seconds))

    embed = create_enhanced_embed(
        title=f"🚫 {ban_type} Ban Issued",
        description=f"A user has been banned from generation features.",
        color=discord.Color.red()
    )

    embed.add_field(name="👤 User", value=f"{user.mention} ({user.id})", inline=True)
    embed.add_field(name="👮 Moderator", value=f"{moderator.mention} ({moderator.id})", inline=True)
    embed.add_field(name="⏱️ Duration", value=duration_text, inline=True)
    embed.add_field(name="📝 Reason", value=reason, inline=False)

    try:
        await ban_logs_channel.send(embed=embed)
    except Exception as e:
        print(f"Error sending ban log: {e}")

# --- Restock Logging Function ---
async def log_restock_event(guild: discord.Guild, user: discord.User, channel: discord.TextChannel, role_mentions: list = None):
    """Log restock events to the restock logs channel."""
    if not RESTOCK_LOGS_CHANNEL_ID:
        return

    restock_logs_channel = guild.get_channel(RESTOCK_LOGS_CHANNEL_ID)
    if not restock_logs_channel:
        return

    role_text = ", ".join([role.mention for role in role_mentions]) if role_mentions else "None"

    embed = create_enhanced_embed(
        title="📦 Restock Command Used",
        description="A restock notification was triggered.",
        color=discord.Color.purple()
    )

    embed.add_field(name="👤 User", value=f"{user.mention} ({user.id})", inline=True)
    embed.add_field(name="📍 Channel", value=f"{channel.mention} ({channel.id})", inline=True)
    embed.add_field(name="🔔 Roles Pinged", value=role_text, inline=False)

    try:
        await restock_logs_channel.send(embed=embed)
    except Exception as e:
        print(f"Error sending restock log: {e}")

# --- DM Ban Notification Function ---
async def send_gen_ban_dm(member: discord.Member, ban_type: str, reason: str, moderator: discord.Member, unban_time: datetime.datetime = None):
    """
    Sends a nice embed to the banned user's DMs.
    """
    try:
        title = "You have been Banned from Generation Commands"
        description = "Your ability to use generation commands has been restricted."
        color = discord.Color.dark_red() if ban_type == "Permanent" else discord.Color.orange()

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.now(EST_TIMEZONE)
        )
        embed.set_author(name=BOT_AUTHOR_NAME, icon_url=EMBED_THUMBNAIL_URL)
        embed.set_thumbnail(url=EMBED_THUMBNAIL_URL)
        embed.set_footer(text=BOT_FOOTER_TEXT_BASE)

        embed.add_field(name="Ban Type", value=ban_type, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)

        if unban_time:
            embed.add_field(name="Expires", value=unban_time.strftime('%Y-%m-%d %I:%M:%S %p EST'), inline=True)
        else:
            embed.add_field(name="Expires", value="Never", inline=True)

        await member.send(embed=embed)
        print(f"Sent ban DM to {member.display_name} ({member.id}).")
    except discord.Forbidden:
        print(f"Could not send ban DM to {member.display_name} ({member.id}) - DMs are closed.")
    except Exception as e:
        print(f"Error sending ban DM to {member.display_name} ({member.id}): {e}")

# --- Bot Events ---
@bot.event
async def on_ready():
    """Event that fires when the bot successfully connects to Discord."""
    bot.start_time = datetime.datetime.now(datetime.timezone.utc)
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    print(f'Bot Prefix: {COMMAND_PREFIX}')
    print(f'Free Generation Channels: {FREE_CHANNEL_IDS}')
    print(f'Premium Generation Channels: {PREMIUM_CHANNEL_IDS}')
    print(f'Booster Generation Channels: {BOOSTER_CHANNEL_IDS}')
    print(f'Restock Notification Channel: {RESTOCK_CHANNEL_ID}')
    print(f'Restock Role: {RESTOCK_ROLE_ID}')
    print(f'Vouch Channel: {VOUCH_CHANNEL_ID}')
    print(f'Log Channel: {LOG_CHANNEL_ID}')
    print(f'Restock Logs Channel: {RESTOCK_LOGS_CHANNEL_ID}')
    print(f'Ban Logs Channel: {BAN_LOGS_CHANNEL_ID}')
    print(f'Vouch Grace Period: {VOUCH_GRACE_PERIOD_SECONDS} seconds')
    print(f'Free Gen Cooldown: {FREE_GEN_COOLDOWN_SECONDS} seconds')
    print(f'Premium Gen Cooldown: {PREMIUM_GEN_COOLDOWN_SECONDS} seconds')
    print(f'Booster Gen Cooldown: {BOOSTER_GEN_COOLDOWN_SECONDS} seconds')
    print(f'Bot Admins: {bot_admin_ids}')
    print(f'Allowed Guild IDs: {ALLOWED_GUILD_IDS}')

    # Set bot status from config
    activity_type = BOT_STATUS_CONFIG.get("type", "playing").lower()
    activity_name = BOT_STATUS_CONFIG.get("name", f"{BOT_FOOTER_TEXT_BASE} | $info")
    activity = None

    if activity_type == "playing":
        activity = discord.Game(name=activity_name)
    elif activity_type == "watching":
        activity = discord.Activity(type=discord.ActivityType.watching, name=activity_name)
    elif activity_type == "listening":
        activity = discord.Activity(type=discord.ActivityType.listening, name=activity_name)
    elif activity_type == "streaming":
        stream_url = BOT_STATUS_CONFIG.get("url")
        if stream_url:
            activity = discord.Streaming(name=activity_name, url=stream_url)
        else:
            print("Warning: Streaming status type requires a 'url' in config.json. Defaulting to 'playing'.")
            activity = discord.Game(name=activity_name)
    else:
        print(f"Warning: Unknown activity type '{activity_type}'. Defaulting to 'playing'.")
        activity = discord.Game(name=activity_name)

    await bot.change_presence(activity=activity)
    print(f"Bot status set to {activity_type.capitalize()}: {activity_name}")

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Bot Started",
            description=f"Bot started successfully with status: **{activity_type.capitalize()}: {activity_name}**",
            color=discord.Color.green(),
            author=bot.user
        )

    # Sync slash commands globally
    print("Syncing slash commands globally...")
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} slash commands globally.")
        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Slash Commands Synced",
                description=f"Successfully synced {len(synced)} slash commands globally.",
                color=discord.Color.blue(),
                author=bot.user
            )
    except Exception as e:
        print(f"Failed to sync slash commands globally: {e}")
        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Slash Sync Failed",
                description=f"Failed to sync slash commands: {e}",
                color=discord.Color.red(),
                author=bot.user
            )

    # Start background tasks
    check_temp_bans.start()
    check_vouch_timers.start()

@bot.event
async def on_message(message: discord.Message):
    """Handles messages for the unified vouch system and processes commands."""
    if message.author.bot:
        return

    # Unified vouch system - only one vouch channel
    if VOUCH_CHANNEL_ID and message.channel.id == VOUCH_CHANNEL_ID:
        user_id = message.author.id

        # Check if message contains "legit" (case-insensitive)
        if "legit" not in message.content.lower():
            await message.add_reaction("❌")

            error_embed = discord.Embed(
                title="❌ Invalid Vouch Message",
                description="Your vouch message must contain the word **\"legit\"** to be valid.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            error_embed.add_field(
                name="📝 Example",
                value=f"Legit got Minecraft from {message.author.mention}",
                inline=False
            )
            error_embed.add_field(
                name="💡 Try Again",
                value="Please send a new message with 'legit' included.",
                inline=False
            )
            error_embed.set_footer(text=EMBED_FOOTER_TEXT, icon_url=EMBED_THUMBNAIL_URL)
            error_embed.set_thumbnail(url=EMBED_THUMBNAIL_URL)
            error_embed.set_author(name=BOT_AUTHOR_NAME, icon_url=EMBED_THUMBNAIL_URL)

            try:
                await message.reply(embed=error_embed, mention_author=True)
            except:
                await message.channel.send(embed=error_embed)

            if LOG_CHANNEL_ID:
                await log_event(
                    event_type="Invalid Vouch Attempt",
                    description=f"User {message.author.mention} attempted to vouch without 'legit' keyword.",
                    color=discord.Color.red(),
                    author=message.author,
                    channel=message.channel
                )
            await bot.process_commands(message)
            return

        # Check if user is banned
        is_banned, ban_data = is_gen_banned(user_id)
        if is_banned:
            await message.add_reaction("✅")
            if user_id in vouch_timers:
                del vouch_timers[user_id]
            if LOG_CHANNEL_ID:
                await log_event(
                    event_type="Vouch (While Banned)",
                    description=f"User {message.author.mention} vouched while generation banned.",
                    color=discord.Color.orange(),
                    author=message.author,
                    channel=message.channel
                )
            await bot.process_commands(message)
            return

        # Process vouch normally
        await message.add_reaction("✅")
        global vouch_count
        vouch_count += 1
        save_vouch_data()

        if user_id in vouch_timers:
            del vouch_timers[user_id]

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Vouch Successful",
                description=f"User {message.author.mention} successfully vouched. Total: {vouch_count}",
                color=discord.Color.green(),
                author=message.author,
                channel=message.channel
            )

    await bot.process_commands(message)

# --- Background Tasks ---
@tasks.loop(seconds=30)
async def check_temp_bans():
    """Background task to automatically unban temporarily banned users."""
    bans = load_gen_bans()
    current_time = int(datetime.datetime.utcnow().timestamp())
    expired_users = []

    for user_id_str, ban_data in list(bans.items()):
        end_ts = ban_data.get("end_ts")
        if end_ts and current_time >= end_ts:
            expired_users.append(int(user_id_str))
            del bans[user_id_str]

    if expired_users:
        save_gen_bans(bans)
        for user_id in expired_users:
            print(f"Temporary ban expired for user ID {user_id}.")
            if LOG_CHANNEL_ID:
                await log_event(
                    event_type="Temp Ban Expired",
                    description=f"Temporary ban automatically expired for user ID {user_id}.",
                    color=discord.Color.blue(),
                    author=bot.user
                )

@tasks.loop(seconds=30)
async def check_vouch_timers():
    """Background task to enforce vouch grace period."""
    current_time = datetime.datetime.now(datetime.timezone.utc)
    expired_vouches = []

    for user_id, generation_time in list(vouch_timers.items()):
        time_since_generation = (current_time - generation_time).total_seconds()
        if time_since_generation >= VOUCH_GRACE_PERIOD_SECONDS:
            expired_vouches.append(user_id)
            del vouch_timers[user_id]

    for user_id in expired_vouches:
        # Add user to temporary ban list (30 minute ban)
        add_gen_ban(user_id, bot.user.id, "Failed to vouch within the required time period", 1800)

        user = bot.get_user(user_id)
        if user:
            try:
                embed = create_enhanced_embed(
                    title="⚠️ Generation Ban Notice",
                    description="You have been temporarily banned from generation commands.",
                    color=discord.Color.red()
                )
                embed.add_field(name="📝 Reason", value="Failed to vouch within the required time period", inline=False)
                embed.add_field(name="⏱️ Duration", value="30 minutes", inline=True)
                embed.add_field(name="⚡ Action Required", value="Please vouch after generating accounts in the future!", inline=False)

                await user.send(embed=embed)
            except Exception:
                pass

            # Log to ban logs channel
            for guild in bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    await log_ban_event(guild, user, bot.user, "Failed to vouch within the required time period", 1800, "Automatic Generation")
                    break

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Vouch Grace Period Expired",
                description=f"User ID {user_id} failed to vouch within {VOUCH_GRACE_PERIOD_SECONDS // 60} minutes and was temporarily banned for 30 minutes.",
                color=discord.Color.red(),
                author=bot.user
            )

# --- Decorators ---
def is_bot_admin():
    """Decorator to check if the user is a bot admin."""
    def predicate(ctx_or_interaction):
        if isinstance(ctx_or_interaction, commands.Context):
            return ctx_or_interaction.author.id in bot_admin_ids
        elif isinstance(ctx_or_interaction, discord.Interaction):
            return ctx_or_interaction.user.id in bot_admin_ids
        return False
    return commands.check(predicate)

def is_free_gen_channel():
    """Decorator to restrict commands to free generation channels."""
    def predicate(ctx_or_interaction):
        if isinstance(ctx_or_interaction, commands.Context):
            return ctx_or_interaction.channel.id in FREE_CHANNEL_IDS
        elif isinstance(ctx_or_interaction, discord.Interaction):
            return ctx_or_interaction.channel.id in FREE_CHANNEL_IDS
        return False
    return commands.check(predicate)

def is_premium_gen_channel():
    """Decorator to restrict commands to premium generation channels."""
    def predicate(ctx_or_interaction):
        if isinstance(ctx_or_interaction, commands.Context):
            return ctx_or_interaction.channel.id in PREMIUM_CHANNEL_IDS
        elif isinstance(ctx_or_interaction, discord.Interaction):
            return ctx_or_interaction.channel.id in PREMIUM_CHANNEL_IDS
        return False
    return commands.check(predicate)

def is_booster_gen_channel():
    """Decorator to restrict commands to booster generation channels."""
    def predicate(ctx_or_interaction):
        if isinstance(ctx_or_interaction, commands.Context):
            return ctx_or_interaction.channel.id in BOOSTER_CHANNEL_IDS
        elif isinstance(ctx_or_interaction, discord.Interaction):
            return ctx_or_interaction.channel.id in BOOSTER_CHANNEL_IDS
        return False
    return commands.check(predicate)

def is_not_gen_banned():
    """Decorator to check if the user is not banned from generation commands."""
    def predicate(ctx_or_interaction):
        if isinstance(ctx_or_interaction, commands.Context):
            user_id = ctx_or_interaction.author.id
        elif isinstance(ctx_or_interaction, discord.Interaction):
            user_id = ctx_or_interaction.user.id
        else:
            return False

        is_banned, _ = is_gen_banned(user_id)
        return not is_banned
    return commands.check(predicate)

# --- Account Generation Commands ---
@bot.hybrid_command(name='free', help='Generate a free account for a specified service.')
@is_free_gen_channel()
@commands.cooldown(1, FREE_GEN_COOLDOWN_SECONDS, commands.BucketType.user)
async def free_gen(ctx: commands.Context, service: str):
    # Check if user is banned first
    is_banned, ban_data = is_gen_banned(ctx.author.id)
    if is_banned:
        end_ts = ban_data.get("end_ts")
        reason = ban_data.get("reason", "No reason provided")

        if end_ts:
            # Temporary ban
            remaining_seconds = end_ts - int(datetime.datetime.utcnow().timestamp())
            days = remaining_seconds // 86400
            hours = (remaining_seconds % 86400) // 3600
            minutes = (remaining_seconds % 3600) // 60

            time_left = []
            if days > 0:
                time_left.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                time_left.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                time_left.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

            time_left_str = ", ".join(time_left) if time_left else "less than a minute"

            embed = create_enhanced_embed(
                title="🚫 Temporarily Banned",
                description="You are currently temporarily banned from using generation commands.",
                color=discord.Color.red(),
                ctx_or_interaction=ctx
            )
            embed.add_field(name="⏱️ Time Remaining", value=time_left_str, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
        else:
            # Permanent ban
            embed = create_enhanced_embed(
                title="🚫 Permanently Banned",
                description="You are permanently banned from using generation commands.",
                color=discord.Color.dark_red(),
                ctx_or_interaction=ctx
            )
            embed.add_field(name="📝 Reason", value=reason, inline=False)

        await ctx.send(embed=embed, ephemeral=True)
        free_gen.reset_cooldown(ctx)
        return
    service_name_formatted = service.lower().replace(" ", "_")
    file_path = get_stock_file_path("free", service_name_formatted)

    accounts = read_accounts_from_file(file_path)
    if not accounts:
        free_gen.reset_cooldown(ctx)
        embed = create_enhanced_embed(
            title="Out of Stock",
            description=f"Sorry, **{service.capitalize()} Free** stock is currently unavailable.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        embed.add_field(name="Try Again", value="Please check back later or contact staff!", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
        return

    account_details = accounts.pop(0)
    write_accounts_to_file(file_path, accounts)

    vouch_timers[ctx.author.id] = datetime.datetime.now(datetime.timezone.utc)

    vouch_channel = bot.get_channel(VOUCH_CHANNEL_ID)
    vouch_link = f"https://discord.com/channels/{ctx.guild.id}/{VOUCH_CHANNEL_ID}" if ctx.guild and VOUCH_CHANNEL_ID else "the vouch channel"

    dm_embed = create_enhanced_embed(
        title=f"{service.capitalize()} Account Generated!",
        description=f"Here's your free {service.capitalize()} account:",
        color=discord.Color.green()
    )

    dm_embed.add_field(name="📋 Account Details", value=f"```\n{account_details}\n```", inline=False)
    dm_embed.add_field(
        name="⚠️ IMPORTANT: Vouch Required!",
        value=f"You must send any message in {vouch_channel.mention if vouch_channel else 'the vouch channel'} within **{VOUCH_GRACE_PERIOD_SECONDS // 60} minutes** to prevent a **30-minute temporary ban**!\n\n[Click here to vouch]({vouch_link})",
        inline=False
    )

    try:
        await ctx.author.send(embed=dm_embed)
        success_embed = create_enhanced_embed(
            title="🎉 Account Sent!",
            description=f"Your free **{service.capitalize()}** account has been sent to your DMs!",
            color=discord.Color.green(),
            ctx_or_interaction=ctx
        )
        success_embed.add_field(name="⏱️ Remember to Vouch!", value=f"Vouch within **{VOUCH_GRACE_PERIOD_SECONDS // 60} minutes** to avoid a temporary ban!", inline=False)
        await ctx.send(embed=success_embed, ephemeral=True)

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Free Generation",
                description=f"User {ctx.author.mention} generated a free {service.capitalize()} account.",
                color=discord.Color.blue(),
                author=ctx.author,
                channel=ctx.channel,
                fields=[{"name": "Service", "value": service.capitalize(), "inline": True}]
            )
    except discord.Forbidden:
        error_embed = create_enhanced_embed(
            title="❌ DM Failed",
            description="Could not send you the account. Please enable DMs from server members!",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=error_embed, ephemeral=True)
        # Return the account to the stock
        accounts.insert(0, account_details)
        write_accounts_to_file(file_path, accounts)
        # Reset cooldown
        free_gen.reset_cooldown(ctx)

@bot.hybrid_command(name='premium', help='Generate a premium account for a specified service.')
@is_premium_gen_channel()
@commands.cooldown(1, PREMIUM_GEN_COOLDOWN_SECONDS, commands.BucketType.user)
async def premium_gen(ctx: commands.Context, service: str):
    # Check if user is banned first
    is_banned, ban_data = is_gen_banned(ctx.author.id)
    if is_banned:
        end_ts = ban_data.get("end_ts")
        reason = ban_data.get("reason", "No reason provided")

        if end_ts:
            # Temporary ban
            remaining_seconds = end_ts - int(datetime.datetime.utcnow().timestamp())
            days = remaining_seconds // 86400
            hours = (remaining_seconds % 86400) // 3600
            minutes = (remaining_seconds % 3600) // 60

            time_left = []
            if days > 0:
                time_left.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                time_left.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                time_left.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

            time_left_str = ", ".join(time_left) if time_left else "less than a minute"

            embed = create_enhanced_embed(
                title="🚫 Temporarily Banned",
                description="You are currently temporarily banned from using generation commands.",
                color=discord.Color.red(),
                ctx_or_interaction=ctx
            )
            embed.add_field(name="⏱️ Time Remaining", value=time_left_str, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
        else:
            # Permanent ban
            embed = create_enhanced_embed(
                title="🚫 Permanently Banned",
                description="You are permanently banned from using generation commands.",
                color=discord.Color.dark_red(),
                ctx_or_interaction=ctx
            )
            embed.add_field(name="📝 Reason", value=reason, inline=False)

        await ctx.send(embed=embed, ephemeral=True)
        premium_gen.reset_cooldown(ctx)
        return
    service_name_formatted = service.lower().replace(" ", "_")
    file_path = get_stock_file_path("premium", service_name_formatted)

    accounts = read_accounts_from_file(file_path)
    if not accounts:
        premium_gen.reset_cooldown(ctx)
        embed = create_enhanced_embed(
            title="Out of Stock",
            description=f"Sorry, **{service.capitalize()} Premium** stock is currently unavailable.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        embed.add_field(name="Try Again", value="Please check back later or contact staff!", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
        return

    account_details = accounts.pop(0)
    write_accounts_to_file(file_path, accounts)

    vouch_timers[ctx.author.id] = datetime.datetime.now(datetime.timezone.utc)

    vouch_channel = bot.get_channel(VOUCH_CHANNEL_ID)
    vouch_link = f"https://discord.com/channels/{ctx.guild.id}/{VOUCH_CHANNEL_ID}" if ctx.guild and VOUCH_CHANNEL_ID else "the vouch channel"

    dm_embed = create_enhanced_embed(
        title=f"{service.capitalize()} Premium Account Generated!",
        description=f"Here's your premium {service.capitalize()} account:",
        color=discord.Color.gold()
    )

    dm_embed.add_field(name="📋 Account Details", value=f"```\n{account_details}\n```", inline=False)
    dm_embed.add_field(
        name="⚠️ IMPORTANT: Vouch Required!",
        value=f"You must send any message in {vouch_channel.mention if vouch_channel else 'the vouch channel'} within **{VOUCH_GRACE_PERIOD_SECONDS // 60} minutes** to prevent a **30-minute temporary ban**!\n\n[Click here to vouch]({vouch_link})",
        inline=False
    )

    try:
        await ctx.author.send(embed=dm_embed)
        success_embed = create_enhanced_embed(
            title="🎉 Premium Account Sent!",
            description=f"Your premium **{service.capitalize()}** account has been sent to your DMs!",
            color=discord.Color.gold(),
            ctx_or_interaction=ctx
        )
        success_embed.add_field(name="⏱️ Remember to Vouch!", value=f"Vouch within **{VOUCH_GRACE_PERIOD_SECONDS // 60} minutes** to avoid a temporary ban!", inline=False)
        await ctx.send(embed=success_embed, ephemeral=True)

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Premium Generation",
                description=f"User {ctx.author.mention} generated a premium {service.capitalize()} account.",
                color=discord.Color.gold(),
                author=ctx.author,
                channel=ctx.channel,
                fields=[{"name": "Service", "value": service.capitalize(), "inline": True}]
            )
    except discord.Forbidden:
        error_embed = create_enhanced_embed(
            title="❌ DM Failed",
            description="Could not send you the account. Please enable DMs from server members!",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=error_embed, ephemeral=True)
        # Return the account to the stock
        accounts.insert(0, account_details)
        write_accounts_to_file(file_path, accounts)
        # Reset cooldown
        premium_gen.reset_cooldown(ctx)

@bot.hybrid_command(name='booster', help='Generate a booster account for a specified service.')
@is_booster_gen_channel()
@commands.cooldown(1, BOOSTER_GEN_COOLDOWN_SECONDS, commands.BucketType.user)
async def booster_gen(ctx: commands.Context, service: str):
    # Check if user is banned first
    is_banned, ban_data = is_gen_banned(ctx.author.id)
    if is_banned:
        end_ts = ban_data.get("end_ts")
        reason = ban_data.get("reason", "No reason provided")

        if end_ts:
            # Temporary ban
            remaining_seconds = end_ts - int(datetime.datetime.utcnow().timestamp())
            days = remaining_seconds // 86400
            hours = (remaining_seconds % 86400) // 3600
            minutes = (remaining_seconds % 3600) // 60

            time_left = []
            if days > 0:
                time_left.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                time_left.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                time_left.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

            time_left_str = ", ".join(time_left) if time_left else "less than a minute"

            embed = create_enhanced_embed(
                title="🚫 Temporarily Banned",
                description="You are currently temporarily banned from using generation commands.",
                color=discord.Color.red(),
                ctx_or_interaction=ctx
            )
            embed.add_field(name="⏱️ Time Remaining", value=time_left_str, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
        else:
            # Permanent ban
            embed = create_enhanced_embed(
                title="🚫 Permanently Banned",
                description="You are permanently banned from using generation commands.",
                color=discord.Color.dark_red(),
                ctx_or_interaction=ctx
            )
            embed.add_field(name="📝 Reason", value=reason, inline=False)

        await ctx.send(embed=embed, ephemeral=True)
        booster_gen.reset_cooldown(ctx)
        return
    service_name_formatted = service.lower().replace(" ", "_")
    file_path = get_stock_file_path("booster", service_name_formatted)

    accounts = read_accounts_from_file(file_path)
    if not accounts:
        booster_gen.reset_cooldown(ctx)
        embed = create_enhanced_embed(
            title="Out of Stock",
            description=f"Sorry, **{service.capitalize()} Booster** stock is currently unavailable.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        embed.add_field(name="Try Again", value="Please check back later or contact staff!", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
        return

    account_details = accounts.pop(0)
    write_accounts_to_file(file_path, accounts)

    vouch_timers[ctx.author.id] = datetime.datetime.now(datetime.timezone.utc)

    vouch_channel = bot.get_channel(VOUCH_CHANNEL_ID)
    vouch_link = f"https://discord.com/channels/{ctx.guild.id}/{VOUCH_CHANNEL_ID}" if ctx.guild and VOUCH_CHANNEL_ID else "the vouch channel"

    dm_embed = create_enhanced_embed(
        title=f"{service.capitalize()} Booster Account Generated!",
        description=f"Here's your booster {service.capitalize()} account:",
        color=discord.Color.purple()
    )

    dm_embed.add_field(name="📋 Account Details", value=f"```\n{account_details}\n```", inline=False)
    dm_embed.add_field(
        name="⚠️ IMPORTANT: Vouch Required!",
        value=f"You must send any message in {vouch_channel.mention if vouch_channel else 'the vouch channel'} within **{VOUCH_GRACE_PERIOD_SECONDS // 60} minutes** to prevent a **30-minute temporary ban**!\n\n[Click here to vouch]({vouch_link})",
        inline=False
    )

    try:
        await ctx.author.send(embed=dm_embed)
        success_embed = create_enhanced_embed(
            title="🎉 Booster Account Sent!",
            description=f"Your booster **{service.capitalize()}** account has been sent to your DMs!",
            color=discord.Color.purple(),
            ctx_or_interaction=ctx
        )
        success_embed.add_field(name="⏱️ Remember to Vouch!", value=f"Vouch within **{VOUCH_GRACE_PERIOD_SECONDS // 60} minutes** to avoid a temporary ban!", inline=False)
        await ctx.send(embed=success_embed, ephemeral=True)

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Booster Generation",
                description=f"User {ctx.author.mention} generated a booster {service.capitalize()} account.",
                color=discord.Color.purple(),
                author=ctx.author,
                channel=ctx.channel,
                fields=[{"name": "Service", "value": service.capitalize(), "inline": True}]
            )
    except discord.Forbidden:
        error_embed = create_enhanced_embed(
            title="❌ DM Failed",
            description="Could not send you the account. Please enable DMs from server members!",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=error_embed, ephemeral=True)
        # Return the account to the stock
        accounts.insert(0, account_details)
        write_accounts_to_file(file_path, accounts)
        # Reset cooldown
        booster_gen.reset_cooldown(ctx)

# --- Stock Command ---
@bot.hybrid_command(name='stock', help='Display current stock levels.')
async def stock_command(ctx: commands.Context):
    stock_data = read_all_stock_data()
    total_stock = stock_data.get('total_stock', 0)

    def get_stock_emoji(count):
        if count == 0:
            return "<a:73288animatedarrowred:1423198630122229842>"
        elif 1 <= count <= 50:
            return "<a:15770animatedarrowyellow:1423198706181869658>"
        elif 51 <= count <= 100:
            return "<a:32877animatedarrowbluelite:1423198814465949756>"
        else:
            return "<a:51047animatedarrowwhite:1423198924075700254>"

    embed = create_enhanced_embed(
        title="📦 Current Stock Levels",
        description=f"**Total Available:** {total_stock} accounts",
        ctx_or_interaction=ctx,
        embed_style="info"
    )

    # Free Services
    free_text = ""
    if stock_data['free']:
        for service, count in stock_data['free'].items():
            emoji = get_stock_emoji(count)
            free_text += f"{emoji} **{service}** → `{count} units`\n"
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Free Services", value=free_text or "<a:73288animatedarrowred:1423198630122229842> None available", inline=True)

    # Premium Services
    premium_text = ""
    if stock_data['premium']:
        for service, count in stock_data['premium'].items():
            emoji = get_stock_emoji(count)
            premium_text += f"{emoji} **{service}** → `{count} units`\n"
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Premium Services", value=premium_text or "<a:73288animatedarrowred:1423198630122229842> None available", inline=True)

    # Booster Services
    booster_text = ""
    if stock_data['booster']:
        for service, count in stock_data['booster'].items():
            emoji = get_stock_emoji(count)
            booster_text += f"{emoji} **{service}** → `{count} units`\n"
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Booster Services", value=booster_text or "<a:73288animatedarrowred:1423198630122229842> None available", inline=True)

    await ctx.send(embed=embed)

# --- Admin Commands for Stock Management ---
@bot.hybrid_command(name='create', help='Create a new service stock file.')
@is_bot_admin()
async def create_command(ctx: commands.Context, service: str, service_type: str):
    service_type_lower = service_type.lower()
    service_name_formatted = service.lower().replace(" ", "_")

    if service_type_lower not in ["free", "premium", "booster"]:
        embed = create_enhanced_embed(
            title="Invalid Service Type",
            description="Choose from: `free`, `premium`, or `booster`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    file_path = get_stock_file_path(service_type_lower, service_name_formatted)
    if os.path.exists(file_path):
        embed = create_enhanced_embed(
            title="Service Already Exists",
            description=f"Service '{service}' already exists in '{service_type}'.",
            color=discord.Color.orange(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    write_accounts_to_file(file_path, [])

    embed = create_enhanced_embed(
        title="✅ Service Created",
        description=f"Successfully created service '{service}' of type '{service_type}'",
        ctx_or_interaction=ctx,
        embed_style="success"
    )
    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Service Created",
            description=f"Service '{service}' ({service_type}) was created by {ctx.author.mention}.",
            color=discord.Color.green(),
            author=ctx.author,
            channel=ctx.channel,
            fields=[{"name": "Service", "value": f"{service} ({service_type})", "inline": True}]
        )

@bot.hybrid_command(name='delete', help='Delete an existing service stock file.')
@is_bot_admin()
async def delete_command(ctx: commands.Context, service_type: str, service: str):
    service_type_lower = service_type.lower()
    service_name_formatted = service.lower().replace(" ", "_")

    if service_type_lower not in ["free", "premium", "booster"]:
        embed = create_enhanced_embed(
            title="Invalid Service Type",
            description="Choose from: `free`, `premium`, or `booster`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    file_path = get_stock_file_path(service_type_lower, service_name_formatted)
    if not os.path.exists(file_path):
        embed = create_enhanced_embed(
            title="Service Not Found",
            description=f"Service '{service}' of type '{service_type}' doesn't exist.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    try:
        os.remove(file_path)
        embed = create_enhanced_embed(
            title="🗑️ Service Deleted",
            description=f"Successfully deleted service '{service}' of type '{service_type}'",
            ctx_or_interaction=ctx,
            embed_style="admin"
        )
        await ctx.send(embed=embed)

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Service Deleted",
                description=f"Service '{service}' ({service_type}) was deleted by {ctx.author.mention}.",
                color=discord.Color.red(),
                author=ctx.author,
                channel=ctx.channel,
                fields=[{"name": "Service", "value": f"{service} ({service_type})", "inline": True}]
            )
    except Exception as e:
        embed = create_enhanced_embed(
            title="Deletion Failed",
            description=f"Error deleting service: {e}",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name='add', help='Add stock to an existing service.')
@is_bot_admin()
async def add_command(ctx: commands.Context, service_type: str, service: str, *, accounts_to_add: str):
    service_type_lower = service_type.lower()
    service_name_formatted = service.lower().replace(" ", "_")

    if service_type_lower not in ["free", "premium", "booster"]:
        embed = create_enhanced_embed(
            title="Invalid Service Type",
            description="Choose from: `free`, `premium`, or `booster`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    file_path = get_stock_file_path(service_type_lower, service_name_formatted)
    if not os.path.exists(file_path):
        embed = create_enhanced_embed(
            title="Service Not Found",
            description=f"Service '{service}' of type '{service_type}' doesn't exist.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        embed.add_field(name="Solution", value=f"Create it first with `{COMMAND_PREFIX}create {service} {service_type}`", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
        return

    new_accounts = [line.strip() for line in accounts_to_add.split('\n') if line.strip()]
    if not new_accounts:
        embed = create_enhanced_embed(
            title="No Accounts Provided",
            description="Please provide accounts to add, one per line.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    current_accounts = read_accounts_from_file(file_path)
    combined_accounts = current_accounts + new_accounts
    write_accounts_to_file(file_path, combined_accounts)

    embed = create_enhanced_embed(
        title="➕ Stock Added Successfully",
        description=f"Added **{len(new_accounts)}** accounts to {service} ({service_type})",
        ctx_or_interaction=ctx,
        embed_style="admin"
    )
    embed.add_field(name="Previous Stock", value=str(len(current_accounts)), inline=True)
    embed.add_field(name="Added", value=str(len(new_accounts)), inline=True)
    embed.add_field(name="New Total", value=str(len(combined_accounts)), inline=True)

    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Stock Added",
            description=f"User {ctx.author.mention} added {len(new_accounts)} accounts to {service} ({service_type}).",
            color=discord.Color.gold(),
            author=ctx.author,
            channel=ctx.channel,
            fields=[{"name": "Service", "value": f"{service} ({service_type})", "inline": True},
                    {"name": "Amount Added", "value": len(new_accounts), "inline": True}]
        )

@bot.command(name='upload_stock', help='Upload stock from a .txt file (one account per line).')
@is_bot_admin()
async def upload_stock_command(ctx: commands.Context, service_type: str, service: str):
    service_type_lower = service_type.lower()
    service_name_formatted = service.lower().replace(" ", "_")

    if service_type_lower not in ["free", "premium", "booster"]:
        embed = create_enhanced_embed(
            title="Invalid Service Type",
            description="Choose from: `free`, `premium`, or `booster`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    file_path = get_stock_file_path(service_type_lower, service_name_formatted)
    if not os.path.exists(file_path):
        embed = create_enhanced_embed(
            title="Service Not Found",
            description=f"Service '{service}' of type '{service_type}' doesn't exist.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        embed.add_field(name="Solution", value=f"Create it first with `{COMMAND_PREFIX}create {service} {service_type}`", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
        return

    if not ctx.message.attachments:
        embed = create_enhanced_embed(
            title="No File Attached",
            description="Please attach a .txt file with accounts (one per line).",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        embed.add_field(name="Usage", value=f"`{COMMAND_PREFIX}upload_stock {service_type} {service}` + attach .txt file", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
        return

    attachment = ctx.message.attachments[0]

    if not attachment.filename.endswith('.txt'):
        embed = create_enhanced_embed(
            title="Invalid File Type",
            description="Only .txt files are accepted.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    try:
        file_content = await attachment.read()
        file_text = file_content.decode('utf-8')

        new_accounts = [line.strip() for line in file_text.split('\n') if line.strip()]

        if not new_accounts:
            embed = create_enhanced_embed(
                title="Empty File",
                description="The uploaded file contains no valid accounts.",
                color=discord.Color.red(),
                ctx_or_interaction=ctx
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        current_accounts = read_accounts_from_file(file_path)
        combined_accounts = current_accounts + new_accounts
        write_accounts_to_file(file_path, combined_accounts)

        embed = create_enhanced_embed(
            title="<:restock:1423626360697393173> Stock Uploaded Successfully",
            description=f"Uploaded **{len(new_accounts)}** accounts to {service} ({service_type})",
            ctx_or_interaction=ctx,
            embed_style="admin"
        )
        embed.add_field(name="<a:32877animatedarrowbluelite:1423198814465949756> Previous Stock", value=str(len(current_accounts)), inline=True)
        embed.add_field(name="<a:15770animatedarrowyellow:1423198706181869658> Added", value=str(len(new_accounts)), inline=True)
        embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> New Total", value=str(len(combined_accounts)), inline=True)
        embed.add_field(name="<a:73288animatedarrowred:1423198630122229842> File Name", value=attachment.filename, inline=False)

        await ctx.send(embed=embed)

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Stock Uploaded (File)",
                description=f"User {ctx.author.mention} uploaded {len(new_accounts)} accounts to {service} ({service_type}) from file {attachment.filename}.",
                color=discord.Color.gold(),
                author=ctx.author,
                channel=ctx.channel,
                fields=[
                    {"name": "Service", "value": f"{service} ({service_type})", "inline": True},
                    {"name": "Amount Added", "value": len(new_accounts), "inline": True},
                    {"name": "File", "value": attachment.filename, "inline": True}
                ]
            )

    except Exception as e:
        embed = create_enhanced_embed(
            title="Upload Failed",
            description=f"Error processing file: {str(e)}",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)

# --- Restock Command ---
@bot.hybrid_command(name='restock', help='Send a restock notification with current stock levels.')
@is_bot_admin()
async def restock_command(ctx: commands.Context):
    stock_data = read_all_stock_data()
    total_stock = stock_data.get('total_stock', 0)

    def get_stock_emoji(count):
        if count == 0:
            return "<a:73288animatedarrowred:1423198630122229842>"
        elif 1 <= count <= 50:
            return "<a:15770animatedarrowyellow:1423198706181869658>"
        elif 51 <= count <= 100:
            return "<a:32877animatedarrowbluelite:1423198814465949756>"
        else:
            return "<a:51047animatedarrowwhite:1423198924075700254>"

    embed = create_enhanced_embed(
        title="🔔 RESTOCK ALERT!",
        description="New accounts are now available! Get yours before they run out!",
        ctx_or_interaction=ctx,
        embed_style="success"
    )

    # Free Services
    free_text = ""
    if stock_data['free']:
        for service, count in stock_data['free'].items():
            emoji = get_stock_emoji(count)
            free_text += f"{emoji} **{service}** → `{count} units`\n"
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Free Services", value=free_text or "<a:73288animatedarrowred:1423198630122229842> None available", inline=True)

    # Premium Services
    premium_text = ""
    if stock_data['premium']:
        for service, count in stock_data['premium'].items():
            emoji = get_stock_emoji(count)
            premium_text += f"{emoji} **{service}** → `{count} units`\n"
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Premium Services", value=premium_text or "<a:73288animatedarrowred:1423198630122229842> None available", inline=True)

    # Booster Services
    booster_text = ""
    if stock_data['booster']:
        for service, count in stock_data['booster'].items():
            emoji = get_stock_emoji(count)
            booster_text += f"{emoji} **{service}** → `{count} units`\n"
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Booster Services", value=booster_text or "<a:73288animatedarrowred:1423198630122229842> None available", inline=True)

    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Total Available", value=f"**{total_stock}** accounts ready to go!", inline=False)
    embed.add_field(name="Quick Start", value="Use generation commands in their respective channels!", inline=False)

    # Send to restock channel if configured
    if RESTOCK_CHANNEL_ID:
        restock_channel = bot.get_channel(RESTOCK_CHANNEL_ID)
        if restock_channel:
            try:
                role_mention = f"<@&{RESTOCK_ROLE_ID}>" if RESTOCK_ROLE_ID else ""
                await restock_channel.send(content=role_mention, embed=embed)

                # Log to restock logs
                role_mentions = [ctx.guild.get_role(RESTOCK_ROLE_ID)] if RESTOCK_ROLE_ID and ctx.guild else []
                await log_restock_event(ctx.guild, ctx.author, restock_channel, role_mentions)

                success_embed = create_enhanced_embed(
                    title="Restock Sent",
                    description=f"Restock notification sent to {restock_channel.mention}!",
                    color=discord.Color.green(),
                    ctx_or_interaction=ctx
                )
                await ctx.send(embed=success_embed, ephemeral=True)
            except Exception as e:
                error_embed = create_enhanced_embed(
                    title="Restock Failed",
                    description=f"Couldn't send to restock channel: {e}",
                    color=discord.Color.red(),
                    ctx_or_interaction=ctx
                )
                await ctx.send(embed=error_embed, ephemeral=True)
    else:
        error_embed = create_enhanced_embed(
            title="Restock Channel Not Configured",
            description="Please configure a restock channel using `$setup-restock-channel`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=error_embed, ephemeral=True)

# --- Vouches Command ---
@bot.hybrid_command(name='vouches', help='Display the total number of community vouches.')
async def vouches_command(ctx: commands.Context):
    embed = create_enhanced_embed(
        title="✨ Community Vouches ✨",
        description=f"Our amazing community has given us **{vouch_count:,}** vouches!",
        ctx_or_interaction=ctx,
        embed_style="vouch"
    )

    embed.add_field(name="💖 Thank You!", value="Every vouch shows trust in our service and helps us grow!", inline=False)
    embed.add_field(name="📢 Show Support", value="Remember to vouch with the word **'legit'** after each generation!", inline=False)
    embed.add_field(name="📝 Example", value="Legit got Netflix from this amazing service!", inline=False)

    await ctx.send(embed=embed)

# --- Configuration Commands ---
@bot.hybrid_command(name='set-restock-logs', help='Set channel for restock logging.')
@is_bot_admin()
async def set_restock_logs(ctx: commands.Context, channel: discord.TextChannel):
    global config, RESTOCK_LOGS_CHANNEL_ID

    config['restock_logs_channel_id'] = channel.id
    save_config(config)
    RESTOCK_LOGS_CHANNEL_ID = channel.id

    embed = create_enhanced_embed(
        title="Restock Logs Channel Set",
        description=f"Restock logs will now be sent to {channel.mention}",
        color=discord.Color.blue(),
        ctx_or_interaction=ctx
    )
    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Config Update",
            description=f"Restock logs channel set to {channel.mention} by {ctx.author.mention}",
            color=discord.Color.blue(),
            author=ctx.author,
            channel=ctx.channel
        )

@bot.hybrid_command(name='set-booster-channel', help='Set channel for booster generation.')
@is_bot_admin()
async def set_booster_channel(ctx: commands.Context, channel: discord.TextChannel):
    global config, BOOSTER_CHANNEL_IDS

    config['booster_channel_ids'] = [channel.id]
    save_config(config)
    BOOSTER_CHANNEL_IDS = [channel.id]

    embed = create_enhanced_embed(
        title="Booster Channel Set",
        description=f"Booster generation will now work in {channel.mention}",
        color=discord.Color.purple(),
        ctx_or_interaction=ctx
    )
    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Config Update",
            description=f"Booster channel set to {channel.mention} by {ctx.author.mention}",
            color=discord.Color.purple(),
            author=ctx.author,
            channel=ctx.channel
        )

@bot.hybrid_command(name='set-ban-logs', help='Set channel for ban logging.')
@is_bot_admin()
async def set_ban_logs(ctx: commands.Context, channel: discord.TextChannel):
    global config, BAN_LOGS_CHANNEL_ID

    config['ban_logs_channel_id'] = channel.id
    save_config(config)
    BAN_LOGS_CHANNEL_ID = channel.id

    embed = create_enhanced_embed(
        title="Ban Logs Channel Set",
        description=f"Ban logs will now be sent to {channel.mention}",
        color=discord.Color.red(),
        ctx_or_interaction=ctx
    )
    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Config Update",
            description=f"Ban logs channel set to {channel.mention} by {ctx.author.mention}",
            color=discord.Color.red(),
            author=ctx.author,
            channel=ctx.channel
        )

@bot.hybrid_command(name='clear-stock', help='Clear all stock for a specific category and service.')
@is_bot_admin()
async def clear_stock(ctx: commands.Context, category: str, service: str):
    category = category.lower()
    if category not in ["free", "premium", "booster"]:
        embed = create_enhanced_embed(
            title="Invalid Category",
            description="Choose from: `free`, `premium`, or `booster`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    file_path = get_stock_file_path(category, service.lower().replace(" ", "_"))

    if not os.path.exists(file_path):
        embed = create_enhanced_embed(
            title="Service Not Found",
            description=f"Service '{service}' in category '{category}' doesn't exist.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    # Get current stock count for logging
    current_accounts = read_accounts_from_file(file_path)
    stock_count = len(current_accounts)

    # Clear the file
    write_accounts_to_file(file_path, [])

    embed = create_enhanced_embed(
        title="Stock Cleared",
        description=f"Successfully cleared all stock for **{service}** in **{category}** category.",
        color=discord.Color.orange(),
        ctx_or_interaction=ctx
    )
    embed.add_field(name="Accounts Removed", value=str(stock_count), inline=True)
    embed.add_field(name="New Stock", value="0", inline=True)

    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Stock Cleared",
            description=f"User {ctx.author.mention} cleared {stock_count} accounts from {service} ({category}).",
            color=discord.Color.orange(),
            author=ctx.author,
            channel=ctx.channel,
            fields=[
                {"name": "Service", "value": f"{service} ({category})", "inline": True},
                {"name": "Accounts Removed", "value": stock_count, "inline": True}
            ]
        )

# --- Moderation Commands ---
@bot.hybrid_command(name='gen-ban', help='Ban a user from generation commands.')
@is_bot_admin()
async def gen_ban_command(ctx: commands.Context, user: discord.Member, reason: str, days: int = 0, hours: int = 0):
    length_seconds = days * 86400 + hours * 3600
    duration_text = "Permanent" if length_seconds == 0 else f"{days} day(s) {hours} hour(s)"

    # Check if already banned
    is_banned, ban_data = is_gen_banned(user.id)
    if is_banned:
        embed = create_enhanced_embed(
            title="Already Banned",
            description=f"{user.mention} is already banned from generation commands.",
            color=discord.Color.orange(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    # Add ban
    add_gen_ban(user.id, ctx.author.id, reason, length_seconds if length_seconds > 0 else None)

    # Send DM to user
    try:
        dm_embed = create_enhanced_embed(
            title="Generation Ban Notice",
            description="You have been banned from using generation commands.",
            color=discord.Color.red()
        )
        dm_embed.add_field(name="Server", value=ctx.guild.name if ctx.guild else "Unknown", inline=True)
        dm_embed.add_field(name="Duration", value=duration_text, inline=True)
        dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
        dm_embed.add_field(name="Reason", value=reason, inline=False)

        await user.send(embed=dm_embed)
    except Exception:
        pass

    # Confirm ban
    embed = create_enhanced_embed(
        title="User Generation Banned",
        description=f"{user.mention} has been banned from generation commands.",
        color=discord.Color.red(),
        ctx_or_interaction=ctx
    )
    embed.add_field(name="Duration", value=duration_text, inline=True)
    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)

    await ctx.send(embed=embed)

    # Log to ban logs channel
    await log_ban_event(ctx.guild, user, ctx.author, reason, length_seconds if length_seconds > 0 else None)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Generation Ban Issued",
            description=f"User {user.mention} was banned from generation by {ctx.author.mention}.",
            color=discord.Color.red(),
            author=ctx.author,
            target=user,
            channel=ctx.channel,
            fields=[
                {"name": "Duration", "value": duration_text, "inline": True},
                {"name": "Reason", "value": reason, "inline": False}
            ]
        )

@bot.hybrid_command(name='gen-unban', help='Remove a user from generation ban.', aliases=['unban-gen'])
@is_bot_admin()
async def gen_unban_command(ctx: commands.Context, user: discord.Member):
    is_banned, ban_data = is_gen_banned(user.id)
    if not is_banned:
        embed = create_enhanced_embed(
            title="Not Banned",
            description=f"{user.mention} is not currently banned from generation commands.",
            color=discord.Color.orange(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    remove_gen_ban(user.id)

    embed = create_enhanced_embed(
        title="Generation Ban Removed",
        description=f"{user.mention} has been unbanned from generation commands.",
        color=discord.Color.green(),
        ctx_or_interaction=ctx
    )
    embed.add_field(name="Unbanned By", value=ctx.author.mention, inline=True)

    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Generation Ban Removed",
            description=f"User {user.mention} was unbanned from generation by {ctx.author.mention}.",
            color=discord.Color.green(),
            author=ctx.author,
            target=user,
            channel=ctx.channel
        )

# --- Set Cooldown Command ---
@bot.hybrid_command(name='set-cooldown', help='Set cooldown for a generation category.')
@is_bot_admin()
async def set_cooldown_command(ctx: commands.Context, category: str, duration: str):
    global config, FREE_GEN_COOLDOWN_SECONDS, PREMIUM_GEN_COOLDOWN_SECONDS, BOOSTER_GEN_COOLDOWN_SECONDS

    category = category.lower()
    if category not in ['free', 'premium', 'booster']:
        embed = create_enhanced_embed(
            title="Invalid Category",
            description="Choose from: `free`, `premium`, or `booster`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    try:
        # Parse duration string (e.g., "1s", "3m", "2h", "1d")
        duration_lower = duration.lower()
        if duration_lower.endswith('s'):
            seconds = int(duration_lower[:-1])
        elif duration_lower.endswith('m'):
            seconds = int(duration_lower[:-1]) * 60
        elif duration_lower.endswith('h'):
            seconds = int(duration_lower[:-1]) * 3600
        elif duration_lower.endswith('d'):
            seconds = int(duration_lower[:-1]) * 86400
        else:
            raise ValueError("Invalid duration format")

        # Update config
        if category == 'free':
            config['free_gen_cooldown_seconds'] = seconds
            FREE_GEN_COOLDOWN_SECONDS = seconds
            free_gen.cooldown = commands.Cooldown(1, seconds)
        elif category == 'premium':
            config['premium_gen_cooldown_seconds'] = seconds
            PREMIUM_GEN_COOLDOWN_SECONDS = seconds
            premium_gen.cooldown = commands.Cooldown(1, seconds)
        elif category == 'booster':
            config['booster_gen_cooldown_seconds'] = seconds
            BOOSTER_GEN_COOLDOWN_SECONDS = seconds
            booster_gen.cooldown = commands.Cooldown(1, seconds)

        save_config(config)

        embed = create_enhanced_embed(
            title="Cooldown Updated",
            description=f"**{category.capitalize()}** generation cooldown set to **{duration}** ({seconds} seconds)",
            color=discord.Color.green(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed)

        if LOG_CHANNEL_ID:
            await log_event(
                event_type="Cooldown Updated",
                description=f"{category.capitalize()} cooldown set to {duration} by {ctx.author.mention}",
                color=discord.Color.blue(),
                author=ctx.author,
                channel=ctx.channel
            )
    except ValueError:
        embed = create_enhanced_embed(
            title="Invalid Duration",
            description="Use format: `5s`, `3m`, `2h`, or `1d`",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)

# --- Admin Management Commands ---
@bot.hybrid_command(name='add-bot-admin', help='Add a user as a bot admin.')
@is_bot_admin()
async def add_bot_admin(ctx: commands.Context, user: discord.Member):
    if user.id in bot_admin_ids:
        embed = create_enhanced_embed(
            title="Already Admin",
            description=f"{user.mention} is already a bot admin.",
            color=discord.Color.orange(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    bot_admin_ids.add(user.id)
    save_bot_admins()

    embed = create_enhanced_embed(
        title="✅ Admin Added",
        description=f"{user.mention} has been added as a bot admin.",
        color=discord.Color.green(),
        ctx_or_interaction=ctx
    )
    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Bot Admin Added",
            description=f"{user.mention} was added as a bot admin by {ctx.author.mention}.",
            color=discord.Color.green(),
            author=ctx.author,
            target=user,
            channel=ctx.channel
        )

@bot.hybrid_command(name='remove-bot-admin', help='Remove a user as a bot admin.')
@is_bot_admin()
async def remove_bot_admin(ctx: commands.Context, user: discord.Member):
    if user.id not in bot_admin_ids:
        embed = create_enhanced_embed(
            title="Not an Admin",
            description=f"{user.mention} is not a bot admin.",
            color=discord.Color.orange(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed, ephemeral=True)
        return

    bot_admin_ids.remove(user.id)
    save_bot_admins()

    embed = create_enhanced_embed(
        title="❌ Admin Removed",
        description=f"{user.mention} has been removed as a bot admin.",
        color=discord.Color.red(),
        ctx_or_interaction=ctx
    )
    await ctx.send(embed=embed)

    if LOG_CHANNEL_ID:
        await log_event(
            event_type="Bot Admin Removed",
            description=f"{user.mention} was removed as a bot admin by {ctx.author.mention}.",
            color=discord.Color.red(),
            author=ctx.author,
            target=user,
            channel=ctx.channel
        )

@bot.hybrid_command(name='list-bot-admins', help='List all bot admins.')
@is_bot_admin()
async def list_bot_admins(ctx: commands.Context):
    if not bot_admin_ids:
        embed = create_enhanced_embed(
            title="No Bot Admins",
            description="There are currently no bot admins.",
            color=discord.Color.orange(),
            ctx_or_interaction=ctx
        )
        await ctx.send(embed=embed)
        return

    admin_list = []
    for admin_id in bot_admin_ids:
        user = bot.get_user(admin_id)
        if user:
            admin_list.append(f"{user.mention} ({user.id})")
        else:
            admin_list.append(f"Unknown User ({admin_id})")

    embed = create_enhanced_embed(
        title="Bot Admins",
        description="\n".join(admin_list),
        color=discord.Color.blue(),
        ctx_or_interaction=ctx
    )
    await ctx.send(embed=embed)

# --- Status Command ---
@bot.command(name='status', help='Display bot status and system information')
async def status_command(ctx: commands.Context):
    try:
        import psutil
        import platform

        # Calculate uptime
        uptime_seconds = int((datetime.datetime.now(datetime.timezone.utc) - bot.start_time).total_seconds())
        uptime_days = uptime_seconds // 86400
        uptime_hours = (uptime_seconds % 86400) // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        uptime_secs = uptime_seconds % 60
        uptime_str = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m {uptime_secs}s"

        # Get system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get bot info
        guild_count = len(bot.guilds)
        user_count = sum(g.member_count for g in bot.guilds)

        embed = create_enhanced_embed(
            title="🤖 Bot Status",
            description="System and bot information",
            color=discord.Color.blue(),
            ctx_or_interaction=ctx
        )

        # Bot Info
        embed.add_field(
            name="📊 Bot Statistics",
            value=f"**Uptime:** {uptime_str}\n"
                  f"**Guilds:** {guild_count}\n"
                  f"**Users:** {user_count:,}\n"
                  f"**Latency:** {round(bot.latency * 1000)}ms",
            inline=True
        )

        # System Info
        embed.add_field(
            name="💻 System",
            value=f"**OS:** {platform.system()} {platform.release()}\n"
                  f"**Python:** {platform.python_version()}\n"
                  f"**Discord.py:** {discord.__version__}",
            inline=True
        )

        # Resource Usage
        embed.add_field(
            name="📈 Resources",
            value=f"**CPU:** {cpu_percent}%\n"
                  f"**RAM:** {memory.percent}% ({memory.used / (1024**3):.2f}GB / {memory.total / (1024**3):.2f}GB)\n"
                  f"**Disk:** {disk.percent}% ({disk.used / (1024**3):.2f}GB / {disk.total / (1024**3):.2f}GB)",
            inline=True
        )

        # Libraries
        embed.add_field(
            name="📚 Libraries",
            value=f"• discord.py v{discord.__version__}\n"
                  f"• aiohttp\n"
                  f"• psutil",
            inline=True
        )

        # Stock Info
        stock_data = read_all_stock_data()
        embed.add_field(
            name="📦 Stock",
            value=f"**Total:** {stock_data.get('total_stock', 0):,}\n"
                  f"**Vouches:** {vouch_count:,}\n"
                  f"**Admins:** {len(bot_admin_ids)}",
            inline=True
        )

        embed.set_footer(text="By SeriesV2", icon_url=EMBED_THUMBNAIL_URL)

        await ctx.send(embed=embed)
    except Exception as e:
        error_embed = create_enhanced_embed(
            title="Status Error",
            description=f"Could not retrieve status: {str(e)}",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        await ctx.send(error_embed)

# --- Info Command ---
@bot.hybrid_command(name='info', help='Display bot information.')
async def info_command(ctx: commands.Context):
    embed = create_enhanced_embed(
        title="ℹ️ Bot Information",
        description=f"Welcome to **{BOT_FOOTER_TEXT_BASE}**!\nYour trusted account generation service.",
        ctx_or_interaction=ctx,
        embed_style="info"
    )

    embed.add_field(
        name="📊 Statistics",
        value=f"**Total Vouches:** {vouch_count:,}\n"
              f"**Servers:** {len(bot.guilds)}\n"
              f"**Total Users:** {sum(g.member_count for g in bot.guilds):,}",
        inline=True
    )

    stock_data = read_all_stock_data()
    embed.add_field(
        name="📦 Stock",
        value=f"**Total Available:** {stock_data.get('total_stock', 0):,}",
        inline=True
    )

    embed.add_field(
        name="⚙️ Features",
        value="• Free Accounts\n• Premium Accounts\n• Booster Accounts\n• Auto Restocks\n• Vouch System",
        inline=True
    )

    embed.add_field(
        name="💡 Quick Start",
        value=f"Use `{COMMAND_PREFIX}help` to see all commands!\n"
              f"Use `{COMMAND_PREFIX}stock` to view available accounts!",
        inline=False
    )

    await ctx.send(embed=embed)

# --- Help Command ---
@bot.hybrid_command(name='help', help='Display available commands.')
async def help_command(ctx: commands.Context):
    is_admin = ctx.author.id in bot_admin_ids

    embed = create_enhanced_embed(
        title="📚 Command List",
        description=f"Here are all available commands for **{BOT_FOOTER_TEXT_BASE}**",
        ctx_or_interaction=ctx
    )

    # Generation Commands
    embed.add_field(
        name="<a:51047animatedarrowwhite:1423198924075700254> Generation Commands",
        value=f"`{COMMAND_PREFIX}free <service>` - Generate free account\n"
              f"`{COMMAND_PREFIX}premium <service>` - Generate premium account\n"
              f"`{COMMAND_PREFIX}booster <service>` - Generate booster account\n"
              f"`{COMMAND_PREFIX}stock` - View current stock",
        inline=False
    )

    # General Commands
    embed.add_field(
        name="<a:32877animatedarrowbluelite:1423198814465949756> General Commands",
        value=f"`{COMMAND_PREFIX}vouches` - View total vouches\n"
              f"`{COMMAND_PREFIX}info` - Bot information\n"
              f"`{COMMAND_PREFIX}status` - Bot status\n"
              f"`{COMMAND_PREFIX}help` - This command list",
        inline=False
    )

    if is_admin:
        # Stock Management
        embed.add_field(
            name="<a:15770animatedarrowyellow:1423198706181869658> Stock Management (Admin)",
            value=f"`{COMMAND_PREFIX}create <service> <type>` - Create new service\n"
                  f"`{COMMAND_PREFIX}delete <type> <service>` - Delete service\n"
                  f"`{COMMAND_PREFIX}add <type> <service> <accounts>` - Add stock (text)\n"
                  f"`{COMMAND_PREFIX}upload_stock <type> <service>` - Upload stock (.txt file)\n"
                  f"`{COMMAND_PREFIX}clear-stock <category> <service>` - Clear stock",
            inline=False
        )

        # Notification Commands
        embed.add_field(
            name="<a:51047animatedarrowwhite:1423198924075700254> Notifications (Admin)",
            value=f"`{COMMAND_PREFIX}restock` - Send restock notification",
            inline=False
        )

        # Configuration Commands
        embed.add_field(
            name="<a:73288animatedarrowred:1423198630122229842> Configuration (Admin)",
            value=f"`{COMMAND_PREFIX}set-restock-logs <channel>` - Set restock logs\n"
                  f"`{COMMAND_PREFIX}set-booster-channel <channel>` - Set booster channel\n"
                  f"`{COMMAND_PREFIX}set-ban-logs <channel>` - Set ban logs\n"
                  f"`{COMMAND_PREFIX}set-cooldown <category> <duration>` - Set cooldown (e.g., 5m, 1h)",
            inline=False
        )

        # Moderation Commands
        embed.add_field(
            name="<a:15770animatedarrowyellow:1423198706181869658> Moderation (Admin)",
            value=f"`{COMMAND_PREFIX}gen-ban <user> <reason> [days] [hours]` - Ban from gen\n"
                  f"`{COMMAND_PREFIX}gen-unban <user>` - Unban from gen",
            inline=False
        )

        # Admin Management
        embed.add_field(
            name="<a:32877animatedarrowbluelite:1423198814465949756> Admin Management (Admin)",
            value=f"`{COMMAND_PREFIX}add-bot-admin <user>` - Add bot admin\n"
                  f"`{COMMAND_PREFIX}remove-bot-admin <user>` - Remove bot admin\n"
                  f"`{COMMAND_PREFIX}list-bot-admins` - List all admins",
            inline=False
        )

    await ctx.send(embed=embed)

# --- Error Handler for Cooldowns ---
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining_seconds = int(error.retry_after)
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        # Determine which category based on the command
        category = "Unknown"
        if ctx.command.name == "free":
            category = "Free"
        elif ctx.command.name == "premium":
            category = "Premium"
        elif ctx.command.name == "booster":
            category = "Booster"

        time_left = []
        if minutes > 0:
            time_left.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0:
            time_left.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        time_left_str = ", ".join(time_left) if time_left else "less than a second"

        embed = create_enhanced_embed(
            title="⏰ Cooldown Active",
            description=f"You're on cooldown for **{category}** generation commands.",
            color=discord.Color.red(),
            ctx_or_interaction=ctx
        )
        embed.add_field(name="⏱️ Time Remaining", value=time_left_str, inline=True)
        embed.add_field(name="💡 Tip", value="Wait for the cooldown to expire before trying again!", inline=False)

        await ctx.send(embed=embed, ephemeral=True)
    elif isinstance(error, commands.CheckFailure):
        # Handle wrong channel errors for generation commands
        if ctx.command and ctx.command.name in ['free', 'premium', 'booster']:
            # Determine which channels to mention
            correct_channels = []
            command_type = ""

            if ctx.command.name == "free":
                correct_channels = [ctx.guild.get_channel(ch_id) for ch_id in FREE_CHANNEL_IDS if ctx.guild.get_channel(ch_id)]
                command_type = "Free"
            elif ctx.command.name == "premium":
                correct_channels = [ctx.guild.get_channel(ch_id) for ch_id in PREMIUM_CHANNEL_IDS if ctx.guild.get_channel(ch_id)]
                command_type = "Premium"
            elif ctx.command.name == "booster":
                correct_channels = [ctx.guild.get_channel(ch_id) for ch_id in BOOSTER_CHANNEL_IDS if ctx.guild.get_channel(ch_id)]
                command_type = "Booster"

            if correct_channels:
                channel_mentions = ", ".join([ch.mention for ch in correct_channels])
                embed = create_enhanced_embed(
                    title="❌ Wrong Channel",
                    description=f"You can't use **{command_type}** generation commands here.",
                    color=discord.Color.red(),
                    ctx_or_interaction=ctx
                )
                embed.add_field(
                    name="📍 Correct Channel(s)",
                    value=f"Please use {command_type} generation in: {channel_mentions}",
                    inline=False
                )
                await ctx.send(embed=embed, ephemeral=True)
        # Silently ignore other check failures
    else:
        # Log other errors
        print(f"Command error: {error}")

# --- Main Bot Run ---
if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: Bot token not configured. Please set 'bot_token' in config.json.")
        exit(1)

    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("Error: Invalid bot token. Please check your token in config.json.")
    except Exception as e:
        print(f"Error starting bot: {e}")

# --- Bot Information Command ---
@bot.hybrid_command(name='botinformation', help='Display detailed bot information including version and uptime.')
async def botinformation_command(ctx: commands.Context):
    bot_version = "V2.1.1"
    bot_creator = "SeriesV2/Series_1"

    uptime_seconds = int((datetime.datetime.now(datetime.timezone.utc) - bot.start_time).total_seconds())
    uptime_days = uptime_seconds // 86400
    uptime_hours = (uptime_seconds % 86400) // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_secs = uptime_seconds % 60

    uptime_str = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m {uptime_secs}s"

    embed = create_enhanced_embed(
        title="🤖 Bot Information",
        description="Detailed information about Wither Cloud Gen Bot",
        color=discord.Color.blue(),
        ctx_or_interaction=ctx
    )

    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Version", value=f"`{bot_version}`", inline=True)
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Creator", value=bot_creator, inline=True)
    embed.add_field(name="<a:51047animatedarrowwhite:1423198924075700254> Uptime", value=uptime_str, inline=True)

    embed.add_field(name="<a:32877animatedarrowbluelite:1423198814465949756> Statistics", value=f"• Total Vouches: `{vouch_count:,}`\n• Total Stock: `{read_all_stock_data().get('total_stock', 0):,}`\n• Bot Admins: `{len(bot_admin_ids)}`", inline=False)

    embed.add_field(name="<a:15770animatedarrowyellow:1423198706181869658> System Info", value=f"• Command Prefix: `{COMMAND_PREFIX}`\n• Categories: Free, Premium, Booster\n• Discord.py Version: `{discord.__version__}`", inline=False)

    await ctx.send(embed=embed)

