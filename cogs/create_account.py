import discord
from discord.ext import tasks, commands
import os, json, datetime
import string, random

import requests
from urllib.parse import urlencode

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(Create_account(bot))

def log(msg: str):
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")

JSON_FILE = "button_message.json"
CHANNEL_ID = 1419348011896803512

CKTOJ_DISCORDBOT = os.environ["CKTOJ_DISCORDBOT"]
FRONTEND = os.environ["FRONTEND"].rstrip('/')
BACKEND = os.environ["BACKEND"].rstrip('/')
HEADERS = {
    "Authorization": f"Bearer {CKTOJ_DISCORDBOT}",
    "Content-Type": "application/json"
}

class signup_button(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    def get_user(self, user):
        resp = requests.get(
            f"{BACKEND}/verify/profile",
            headers=HEADERS,
            params=dict(discord_id=user.id))
        
        try: return resp.json()
        except requests.exceptions.JSONDecodeError: return None
    
    def create_verify(self, user):
        resp = requests.post(
            f"{BACKEND}/verify/create",
            headers=HEADERS,
            json={"discord_id": user.id},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        secret = data.get("secret")
        return secret
    
    async def button_handler(self, interaction, type):
        try:
            secret = self.create_verify(interaction.user)
            params = urlencode({"type":type, "secret": secret, "discord_id": interaction.user.id})
            link = f"{FRONTEND}/confirm?{params}"

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Xác thực tài khoản", url=link, style=discord.ButtonStyle.link))

            await interaction.response.send_message("Nhấn nút để xác thực tài khoản (hết hạn 5 phút).", view=view, ephemeral=True)
        except Exception as e:
            log(f"Failed to create verify link for {interaction.user.id}: {e}")
            await interaction.response.send_message("Có lỗi khi tạo link xác thực, vui lòng thử lại sau.", ephemeral=True)

    @discord.ui.button(label="Sign up", style=discord.ButtonStyle.green, custom_id="signup_click")
    async def signup_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.get_user(interaction.user):
            return await interaction.response.send_message("Bạn đã có tài khoản.", ephemeral=True)
        return await self.button_handler(interaction, "create_account")

    
    @discord.ui.button(label="Change password", style=discord.ButtonStyle.primary, custom_id="changepassword_click")
    async def changepassword_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.get_user(interaction.user):
            return await interaction.response.send_message("Bạn chưa có tài khoản mà?", ephemeral=True)
        return await self.button_handler(interaction, "change_password")
        


class Create_account(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
    
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

    @tasks.loop(minutes=5)
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
