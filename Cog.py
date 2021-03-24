import discord
from discord.ext import commands
import random
import asyncio


class SortingHat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.houses = []
        self.leaders = []
        self.category = None

    @commands.Cog.listener()
    async def on_connect(self):
        print("Connected")
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        print("Seeded")
        random.seed()

    @commands.command("obtener")
    async def assign(self, ctx):
        print("Assigning house")
        self.assign_house(ctx, ctx.author)

    @commands.command("categoria")
    @commands.has_permissions(administrator=True)
    async def assign_category_channel(self, ctx, category_id):
        self.category = ctx.guild.get_channel(category_id)
        if self.category is None:
            await ctx.send("No se encontró la categoría")
        else:
            await ctx.send("Se asignó la categoría")

    @commands.command("crear")
    @commands.has_permissions(administrator=True)
    async def create_houses(self, ctx, *, leader: discord.Member = None):
        if leader is None:
            leader = ctx.author
        await ctx.send("Creando casa para {}".format(leader.mention))
        await self.create_all(ctx, leader)
        self.leaders.append(leader)
        await ctx.send("¡Se ha creado la casa {}!".format(leader.name))

    @commands.command("mencionar")
    @commands.has_permissions(administrator=True)
    async def mention(self, ctx, *, leader: discord.Member = None):
        await ctx.send("Recibiendo miembro: {}".format("hola"))

    @commands.command("asignacion_masiva")
    @commands.has_permissions(administrator=True)
    async def assign_massive(self, ctx):
        for member in ctx.guild.members:
            self.assign_house(ctx, member)

    async def create_all(self, ctx, leader):
        if leader in self.leaders:
            await ctx.send("¡Líder: {} ya tiene asignado casa!".format(leader.name))
            return
        role, leader_role = await self.create_roles(ctx, leader)
        print("Creados los roles")
        await self.create_house_channels(ctx, role, leader_role, self.category)

    async def create_house_channels(self, ctx, role, leader_role, category):
        permission_overwrites = {
            role: discord.PermissionOverwrite(read_messages=True),
            leader_role: discord.PermissionOverwrite(
                read_messages=True, manage_roles=True, manage_channels=True)
        }
        await ctx.guild.create_text_channel(
            "casa-{}".format(role.name), overwrites=permission_overwrites, category=category, reason="Creación  de casa.")
        print("Creados los canales de texto")
        await ctx.guild.create_voice_channel(
            "casa-{}".format(role.name), overwrites=permission_overwrites, category=category, reason="Creación  de casa.")
        print("Creados los canales")

    async def create_roles(self, ctx, leader):
        role_name = leader.name
        leader_role_name = "{}_lider".format(role_name)
        print("Creating roles for: {}".format(role_name))
        role = await ctx.guild.create_role(name=role_name)
        print("Created role")
        leader_role = await ctx.guild.create_role(name=leader_role_name)
        await leader.add_roles(leader_role, reason="Registro de lider a casa.")
        return role, leader_role

    def get_total(self):
        return sum([h.count for h in houses])

    async def assign_house(self, ctx, member):
        # Check that we actually have roles to work with
        if len(self.houses) == 0:
            await ctx.send("¡No hay roles registrados!")
            return
        if any(house.role in ctx.author.roles for house in self.houses):
            await ctx.send("¡Ya fuiste asignado a una casa!")
            return

        total = self.get_total()
        previous = 0
        random_select = random.random()
        selected = self.houses[-1]
        for h in houses:
            previous = h.ponder(previous, total)
            if random_select < previous:
                selected = h
                break

        selected.count += 1
        # We've already selected a house, but for dramatic purposes we delay it a little bit.
        await ctx.send("Escogiendo el lugar adecuado para ti.")
        await asyncio.sleep(random.randint(0.2, 2))
        await ctx.send("¡{}!".format(selected.mention))
        await member.add_roles(selected, reason="Registro a casa.")


class House:
    def __init__(self, role, leader_role, count):
        self.role = role
        self.leader_role = leader_role
        self.count = count
        self.random = 0

    def ponder(self, previous, maxCount):
        self.random = previous + (1-(count / maxCount))
        return self.random
