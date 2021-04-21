import discord
from discord.ext import commands
from Cog import SortingHat
from Persistence import JsonPersistence
import os

token = os.getenv("SortingHatKey")
token = "ODIzODUwNDE1MzE2NTMzMzAx.YFm0fQ.8_BZ_av9FUOIwN5yS8pDfC6p1Fk"

if token is not None:
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    bot.add_cog(SortingHat(bot,  JsonPersistence()))
    bot.run(token)
