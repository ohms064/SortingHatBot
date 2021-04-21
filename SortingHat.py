import discord
from discord.ext import commands
from Cog import SortingHat
from Persistence import JsonPersistence
import os

token = os.getenv("SortingHatKey")

if token is not None:
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    bot.add_cog(SortingHat(bot,  JsonPersistence()))
    bot.run(token)
