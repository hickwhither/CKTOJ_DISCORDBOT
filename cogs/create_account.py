import discord
from discord.ext import tasks, commands
import os, json, datetime
import string, random

from werkzeug.security import generate_password_hash
from google.cloud.firestore import FieldFilter
import firebase_admin
from firebase_admin import credentials, firestore

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(Create_account(bot))

def log(msg: str):
    """Print with timestamp"""
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")

def generate_password(length: int = 12) -> str:
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

CERT = "cktoj-users-abcxyzhehe-firebase-adminsdk.json"
JSON_FILE = "button_message.json"
CHANNEL_ID = 1419348011896803512

class SignupModal(discord.ui.Modal):
    def __init__(self, cog):
        super().__init__(title="Create CKTOJ Account")
        self.cog = cog
        
        self.username = discord.ui.TextInput(
            label="Username",
            placeholder="Enter your desired username",
            min_length=3,
            max_length=20,
            required=True,
        )
        self.add_item(self.username)

    async def on_submit(self, interaction: discord.Interaction):
        if self.cog.check_account_exists(interaction.user.id):
            await interaction.response.send_message("You already have an account!", ephemeral=True)
            return

        success, password = await self.cog.create_account(interaction.user.id, str(self.username.value))
        
        if not success:
            await interaction.response.send_message("Failed to create account. Please try again later.", ephemeral=True)
            return

        try:
            embed = discord.Embed(
                title="Account Created Successfully! 🎉",
                description="Your CKTOJ account has been created. Please keep these credentials safe.",
                color=discord.Color.green()
            )
            embed.add_field(name="Username", value=self.username.value, inline=False)
            embed.add_field(name="Password", value=f"||{password}||", inline=False)
            embed.set_footer(text="⚠️ Please keep this information safe and do not share it with anyone!")
            await interaction.user.send(embed=embed)

            await interaction.response.send_message("Account created successfully! Check your DMs for your credentials.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Account created but I couldn't send you a DM! Please enable DMs from server members to receive your credentials.", ephemeral=True)

class signup_button(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Sign up", style=discord.ButtonStyle.green, custom_id="my_button")
    async def signup_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog('Create_account')
        if not cog:
            return await interaction.response.send_message("Account creation system is currently unavailable.", ephemeral=True)
        
        if cog.check_account_exists(interaction.user.id):
            return await interaction.response.send_message("You already have an account!", ephemeral=True)

        await interaction.response.send_modal(SignupModal(cog))


class Create_account(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(CERT)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.users_ref = self.db.collection("user")
        
    def check_account_exists(self, user_id: int) -> bool:
        """Check if a user already has an account"""
        try:
            # Query by discord_id
            docs = self.users_ref.where(filter=FieldFilter("discord_id", "==", user_id)).get()
            return len(docs) > 0
        except Exception as e:
            log(f"Error checking account existence: {e}")
            return False

    async def create_account(self, user_id: int, username: str) -> tuple[bool, str]:
        password = generate_password()
        account_data = {
            "discord_id": user_id,
            "username": username,
            "password": generate_password_hash(password),
            "created_at": datetime.datetime.now()
        }
        
        try:
            # Add a new document with auto-generated ID
            self.users_ref.add(account_data)
            return True, password
        except Exception as e:
            log(f"Error creating account: {e}")
            return False, ""
    
    async def cog_load(self):
        self.bot.add_view(signup_button())
        self.check_button.start()
    def cog_unload(self): self.check_button.cancel()

    def load_message_id(self):
        if not os.path.exists(JSON_FILE):
            return None
        with open(JSON_FILE, "r") as f:
            return json.load(f).get("message_id")
    def save_message_id(self, msg_id: int):
        with open(JSON_FILE, "w") as f:
            json.dump({"message_id": msg_id}, f)

    @tasks.loop(seconds=5)
    async def check_button(self):
        """Check every minute if the button exists"""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(CHANNEL_ID)
        if channel is None:
            log("⚠ Channel not found")
            return

        msg_id = self.load_message_id()
        if msg_id:
            try:
                await channel.fetch_message(msg_id)
                log("🧕 Button message still exists")
                return
            except discord.NotFound:
                log("❌ Button message not found, re-sending...")

        view = signup_button()
        msg = await channel.send(view=view)
        self.save_message_id(msg.id)
        log(f"✅ Sent new button message with id {msg.id}")
