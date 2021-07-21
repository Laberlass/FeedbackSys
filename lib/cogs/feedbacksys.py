
import discord
import sqlite3

from datetime import datetime

from discord import Member, Embed
from discord.ext.commands import Cog
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions

from ..db import db

class Feedbacksys(Cog):
	def __init__(self, bot):
		self.bot = bot

	@command(name="setfeedbackchannel")
	async def setfeedbackchannel_command(self, ctx, channel: discord.TextChannel):
		try:
			db.execute("INSERT INTO feedback_channel VALUES (?, ?)", ctx.guild.id, channel.id)

			embed = Embed(title = "**Success**",
						  description = f"✅ Successfully set feedback channel: {channel.mention}",
						  colour=discord.Color.green(),
						  timestamp=datetime.utcnow())

			await ctx.send(embed=embed)

		except sqlite3.IntegrityError:
			embed = Embed(title = "**Error**",
						  description = f"❌ This Guild already has a feedback channel.",
						  colour=discord.Color.red(),
						  timestamp=datetime.utcnow())

			await ctx.send(embed=embed)

	@command(name="feedback")
	@has_permissions(ban_members=True)
	async def feedback_command(self, ctx, message: discord.Message, *, feedback):
		await ctx.message.delete()
		feedback_channel_id = db.field("SELECT ChannelID FROM feedback_channel WHERE GuildID = ?", ctx.guild.id)
		if feedback_channel_id != None:
			if message.channel.id == feedback_channel_id:
				embed = message.embeds
				embed = embed[0]
				embed.set_field_at(0, name=f"Staff Answer ({ctx.author})", value=f":arrow_right: {feedback}")
				await message.edit(embed=embed)

				embed = Embed(title = "**Success**",
							  description = f"✅ Successfully added feedback",
							  colour=discord.Color.green(),
							  timestamp=datetime.utcnow())

				msg = await ctx.send(embed=embed)
				await msg.delete(delay=1)

			else:
				embed = Embed(title = "**Error**",
							  description = f"❌ This message is not a valid feedback message.",
							  colour=discord.Color.red(),
							  timestamp=datetime.utcnow())

				await ctx.send(embed=embed)

		else:
			embed = Embed(title = "**Error**",
						  description = f"❌ This Guild doesnt have a feedback channel.\nSet a feedback channel with: `{ctx.prefix}setfeedbackchannel <channel>`",
						  colour=discord.Color.red(),
						  timestamp=datetime.utcnow())

			await ctx.send(embed=embed)


	@Cog.listener("on_message")
	async def feedback(self, message):
		if not message.author.bot:
			feedback_channel_id = db.field("SELECT ChannelID FROM feedback_channel WHERE GuildID = ?", message.guild.id)
			if feedback_channel_id != None:
				prefix = db.field("SELECT Prefix FROM guilds WHERE GuildID = ?", message.guild.id)
				if not message.content.startswith(f"{prefix}feedback "):
					if message.channel.id == feedback_channel_id:
						embed = Embed(title=f"New feedback by {message.author}",
				                      description=f"> `{message.content}`",
				 					  colour=message.author.colour,
				 					  timestamp=datetime.utcnow())

						embed.set_thumbnail(url=message.author.avatar_url)

						embed.add_field(name="Staff Answer", value=":arrow_right: Not yet reviewed")
						embed.set_footer(text=message.guild, icon_url=message.guild.icon_url)

						await message.delete()
						await message.channel.send(embed=embed)



	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("feedbacksys")


def setup(bot):
	bot.add_cog(Feedbacksys(bot))
