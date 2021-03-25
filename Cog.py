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
        self.channels = []
        self.next_name = ""

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
        self.assign_house(ctx, ctx.author, False)

    @commands.command("categoria")
    @commands.has_permissions(administrator=True)
    async def assign_category_channel(self, ctx, category_id: int):
        self.category = ctx.guild.get_channel(category_id)
        if self.category is None:
            await ctx.send("No se encontró la categoría")
        else:
            await ctx.send("Se asignó la categoría {}".format(self.category))

    @commands.command("crear_casa")
    async def create_named_house(self, ctx, *name: str):
        self.next_name = "-".join(name).lower()
        await self.create_houses(ctx)
        self.next_name = ""

    @commands.command("crear")
    @commands.has_permissions(administrator=True)
    async def create_houses(self, ctx, *, leader: discord.Member = None):
        if leader is None:
            leader = ctx.author
        await ctx.send("Creando casa para {}".format(leader.name))
        await self.create_all(ctx, leader)
        self.leaders.append(leader)
        await ctx.send("¡Se ha creado la casa {}!".format(leader.name))

    @commands.command("asignacion_masiva")
    @commands.has_permissions(administrator=True)
    async def assign_massive(self, ctx):
        if len(self.leaders) == 0:
            await ctx.send("No hay líderes registrados")
        for member in ctx.guild.members:
            await self.assign_house(ctx, member, True)

    @commands.command("borrar_casas")
    @commands.has_permissions(administrator=True)
    async def remove_all(self, ctx):
        for house in self.houses:
            await house.role.delete()
            await house.leader_role.delete()
        for channel in self.channels:
            await channel.delete()
        self.houses.clear()
        self.channels.clear()
        self.leaders.clear()
        await ctx.send("Se borraron todas las casas")

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
        text_channel = await ctx.guild.create_text_channel(
            "casa-{}".format(role.name), overwrites=permission_overwrites, category=category, reason="Creación  de casa.")
        self.channels.append(text_channel)
        print("Creados los canales de texto")
        voice_channel = await ctx.guild.create_voice_channel(
            "casa-{}".format(role.name), overwrites=permission_overwrites, category=category, reason="Creación  de casa.")
        self.channels.append(voice_channel)
        print("Creados los canales")
        self.houses.append(House(role, leader_role, 1))

    async def create_roles(self, ctx, leader):
        role_name = self.next_name if self.next_name else leader.name
        leader_role_name = "{}_lider".format(role_name)
        print("Creating roles for: {}".format(role_name))
        role = await ctx.guild.create_role(name=role_name)
        print("Created role")
        leader_role = await ctx.guild.create_role(name=leader_role_name)
        await leader.add_roles(leader_role, role, reason="Registro de lider a casa.")
        return role, leader_role

    def get_total(self):
        return sum([h.count for h in self.houses])

    async def assign_house(self, ctx, member, silent):
        # Check that we actually have roles to work with
        if len(self.houses) == 0:
            await ctx.send("¡No hay roles registrados!")
            return
        result = [house.role for house in self.houses if house.role in member.roles]
        if len(result) > 0:
            await ctx.send("¡Ya fuiste asignado a una casa! {}".format(member.name))
            return

        total = self.get_total()
        previous = 0
        random_select = random.random()
        selected = random.choices(
            self.houses, weights=[weights.ponder(total) for weights in self.houses], k=1)[0]
        selected.count += 1
        # We've already selected a house, but for dramatic purposes we delay it a little bit.
        if not silent:
            await ctx.send("Escogiendo el lugar adecuado para ti {}.".format(member.name))
        await asyncio.sleep(random.random()*1.8 + 0.2)
        await ctx.send("¡{} ,eres de la casa: {}!".format(member.name, selected.role.name))
        await member.add_roles(selected.role, reason="Registro a casa.")


class House:
    def __init__(self, role, leader_role, count):
        self.role = role
        self.leader_role = leader_role
        self.count = count

    def ponder(self, maxCount):
        return self.count / maxCount
