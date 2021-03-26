import discord
from discord.ext import commands
import random
import asyncio
from Cog import SortingHat
from Persistence import JsonPersistence

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
token = ""
with open("Ids/discord_key.txt", "r") as f:
    token = f.read()


bot.add_cog(SortingHat(bot,  JsonPersistence()))
bot.run(token)
