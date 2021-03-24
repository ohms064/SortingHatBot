import discord
from discord.ext import commands
import random
import asyncio
from Cog import SortingHat

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
token = ""


bot.add_cog(SortingHat(bot))
bot.run(token)
