import discord
from discord import app_commands
from discord.ext import tasks, commands
import os, json, datetime
import string, random

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(AccountManager(bot))

class AccountManager(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
        self.db = firestore.client()
        self.users_ref = self.db.collection("user")
        # self.bot.tree.add_command(self.remove_account)

    
    async def delete_account(self, discord_id: int) -> bool:
        """Delete a user's account from the database"""
        try:
            # Query for documents with matching discord_id
            docs = self.users_ref.where(filter=FieldFilter("discord_id", "==", discord_id)).get()
            
            if not docs:
                return False
                
            # Delete all matching documents
            for doc in docs:
                doc.reference.delete()
            return True
        except Exception as e:
            print(f"Error deleting account: {e}")
            return False
    
    @app_commands.command(
        name="remove_account",
        description="[Admin] Remove a user's CKTOJ account"
    )
    async def remove_account(
        self, 
        itr: discord.Interaction,
        user: discord.Member = None
    ):
        # Check if user has the admin role (1418853945295634432)
        admin_role = itr.guild.get_role(1418853945295634432)
        if admin_role not in itr.user.roles:
            await itr.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return
        if not user:
            await itr.response.send_message("❌ Please specify a user whose account you want to delete.", ephemeral=True)
            return

        success = await self.delete_account(user.id)        
        if success:
            # Send a DM to the user whose account was deleted
            await itr.response.send_message(content=f"✅ Successfully deleted CKTOJ account for {user.mention}.", ephemeral=True)
            
            try:
                await user.send(f"Your CKTOJ account has been deleted by an administrator")
            except discord.Forbidden:
                pass  # Can't send DM to the user
                
        else:
            await itr.response.send_message(content=f"❌ Failed to delete account. Either {user.mention} doesn't have an account or an error occurred.", ephemeral=True)

    async def on_tree_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
        else:
            await ctx.respond("❌ An error occurred while executing the command.", ephemeral=True)
    
