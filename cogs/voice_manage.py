import discord
from discord import app_commands
from discord.ext import commands
import asyncio

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceManager(bot))

def has_ban_role():
    """Check if user has the ban role (1275798993330376775) or is bot owner"""
    async def predicate(ctx):
        # Check if bot owner
        if await ctx.bot.is_owner(ctx.author):
            return True
        # Check if has the ban role
        role = ctx.guild.get_role(1275798993330376775)
        return role and role in ctx.author.roles
    return commands.check(predicate)

class VoiceManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active_bans = {}  # user_id: {'task': task, 'original_channel': channel, 'user_roles': roles}

    async def _complete_ban(self, user: discord.Member, original_channel: discord.VoiceChannel, user_roles: list):
        """Complete the ban process after 36 seconds"""
        try:
            await asyncio.sleep(36)
            if user.voice and user.voice.channel.id == 1275798785888358539:  # Check if still in target channel
                await user.move_to(original_channel)
                
            # Add roles back
            try:
                await user.add_roles(*user_roles, reason="Restoring roles after ban36")
            except discord.Forbidden:
                pass  # Can't send message here since no ctx
            except Exception:
                pass
        finally:
            # Clean up
            self.active_bans.pop(user.id, None)

    @commands.command()
    @has_ban_role()
    async def ban36(self, ctx: commands.Context, user: discord.Member ):  
        if user.id in self.active_bans:
            await ctx.send(f"❌ {user.mention} is already in a ban36 period.")
            return
        
        # Get target channel
        target_channel = ctx.guild.get_channel(1275798785888358539)
        if not target_channel or not isinstance(target_channel, discord.VoiceChannel):
            await ctx.send("❌ Target channel not found or is not a voice channel.")
            return
        
        # Check in any voice chat
        if not user.voice or not user.voice.channel:
            await ctx.send(f"❌ {user.mention} is not in a voice channel.")
            return
        
        original_channel = user.voice.channel
        user_roles = [role for role in user.roles if role != ctx.guild.default_role]
        
        try:
            await user.remove_roles(*user_roles, reason="Temporary ban36")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage roles.")
            return
        except Exception as e:
            await ctx.send(f"❌ An error occurred while removing roles: {str(e)}")
            return

        try:
            await user.move_to(target_channel)
            await ctx.send(f"✅ Successfully moved {user.mention} to {target_channel.mention}. Moving back in 36 seconds.")
            
            # Create task for completion
            task = asyncio.create_task(self._complete_ban(user, original_channel, user_roles))
            self.active_bans[user.id] = {
                'task': task,
                'original_channel': original_channel,
                'user_roles': user_roles
            }
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to move members.")
            # Restore roles if move failed
            try:
                await user.add_roles(*user_roles, reason="Restoring roles due to move failure")
            except:
                pass
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")
            # Restore roles if error
            try:
                await user.add_roles(*user_roles, reason="Restoring roles due to error")
            except:
                pass

    @commands.command()
    @has_ban_role()
    async def cancel_ban36(self, ctx: commands.Context, user: discord.Member):
        """Cancel an ongoing ban36 for a user"""
        if user.id not in self.active_bans:
            await ctx.send(f"❌ {user.mention} is not currently in a ban36 period.")
            return
        
        ban_data = self.active_bans[user.id]
        task = ban_data['task']
        original_channel = ban_data['original_channel']
        user_roles = ban_data['user_roles']
        
        # Cancel the task
        task.cancel()
        
        # Move back and restore roles
        try:
            if user.voice and user.voice.channel.id == 1275798785888358539:
                await user.move_to(original_channel)
            
            await user.add_roles(*user_roles, reason="Canceling ban36 - restoring roles")
            await ctx.send(f"✅ Canceled ban36 for {user.mention} and restored their roles.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to move members or manage roles.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while canceling: {str(e)}")
        finally:
            # Clean up
            self.active_bans.pop(user.id, None)