import os, importlib
import time, random, string
import discord
from discord import Message, Object
from discord.ext.commands import Bot


class CKTOJ(Bot):
    secret: dict
    def __init__(self, id, prefix):
        self.start_time = time.time()
        print(prefix)
        self.default_prefix = prefix
        super().__init__(
            command_prefix = self.default_prefix,
            intents = discord.Intents.all(),
            application_id = id
        )
    
    async def on_message(self, message: Message):
        if message.content.startswith(self.default_prefix):
            message.content = self.default_prefix + message.content[len(self.default_prefix):].strip()
            await self.process_commands(message)

    async def setup_hook(self):
        self.extra_log = []
        for file in os.listdir('cogs'):
            if not file.startswith('_') and (os.path.exists(os.path.join('cogs', file)) or file.endswith('.py')):
                if file.endswith('.py'): file = file[:-3]
                try:
                    await self.load_extension(f'cogs.{file}')
                    print(f'✅ Loaded {file}')
                except Exception as e:
                    print(f'❌ Error {file}: {e}')
        
        print()
        for extra in self.extra_log:
            print(f"From {extra[0]}:\n{extra[1]}")



    async def on_ready(self):
        print(f'=== Logged as {self.user} ({self.user.id}) ===')
    


import os, json

from dotenv import load_dotenv
load_dotenv()

if __name__ == '__main__':
    BOT_ID = os.environ['BOT_ID']
    BOT_TOKEN = os.environ['BOT_TOKEN']
    PREFIX = os.environ['PREFIX']
    
    bot = CKTOJ(BOT_ID, PREFIX)

    bot.run(BOT_TOKEN)