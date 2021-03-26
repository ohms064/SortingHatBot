import discord
from discord.ext import commands
import random
import asyncio


class SortingHat(commands.Cog):
    def __init__(self, bot, persistence):
        self.bot = bot
        self.houses = {}
        self.category = {}
        self.next_name = ""
        self.persistence = persistence

    @commands.Cog.listener()
    async def on_connect(self):
        print("Connected")
        pass

    @commands.Cog.listener()
    async def on_disconnect(self):
        print("Disconnected")
        for guild in self.bot.guilds:
            await self.save_state(guild.id)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Seeded")
        random.seed()
        for guild in self.bot.guilds:
            guild_id, category_id, houses_ids = self.persistence.load_data(
                guild.id)
            if guild_id is None:
                self.houses[guild.id] = []
                self.category[guild.id] = None
                print("{} has no houses".format(guild.id))
                continue
            self.category[guild_id] = guild.get_channel(category_id)
            self.houses[guild_id] = []
            for house_ids in houses_ids:
                house_ids["guild"] = guild
                house = await self.house_from_ids(** house_ids)
                self.houses[guild_id].append(house)
            for h in self.houses[guild_id]:
                print(h.convert_id_dict())

        print("ready")

    @commands.command("obtener")
    async def assign(self, ctx):
        print("Assigning house")
        self.assign_house(ctx, ctx.author, False)
        await self.save_state(ctx.guild.id)

    @commands.command("categoria")
    @commands.has_permissions(administrator=True)
    async def assign_category_channel(self, ctx, category_id: int):
        self.category[ctx.guild.id] = ctx.guild.get_channel(category_id)
        if self.category[ctx.guild.id] is None:
            await ctx.send("No se encontró la categoría")
        else:
            await ctx.send("Se asignó la categoría {}".format(self.category[ctx.guild.id]))
            await self.save_state(ctx.guild.id)

    @commands.command("nombre")
    async def change_name(self, ctx, role: discord.Role, *name: str):
        house = next(
            (h for h in self.houses[ctx.guild.id] if role == h.role), None)
        if house is None:
            await ctx.send("¡La casa no está registrada!")
            return
        print(ctx.author.roles)
        print("role of type {}: {}".format(
            type(role), role))
        for r in ctx.author.roles:
            print("r of type {}: {}".format(
                type(r), r))

        if role not in ctx.author.roles:
            await ctx.send("No eres lider de esta casa!")
            return
        await house.change_name("-".join(name).lower())

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
        if leader in self.get_leaders(ctx):
            await ctx.send("¡Ya eres lider de una casa!")
            return
        await ctx.send("Creando casa para {}".format(leader.name))
        role, leader_role, text_channel, voice_channel = await self.create_all(ctx, leader)
        self.houses[ctx.guild.id].append(
            House(role, leader_role, text_channel, voice_channel, leader))
        await self.save_state(ctx.guild.id)
        await ctx.send("¡Se ha creado la casa {}!".format(leader.name))

    @commands.command("asignacion_masiva")
    @commands.has_permissions(administrator=True)
    async def assign_massive(self, ctx):
        if len(self.get_leaderes()) == 0:
            await ctx.send("No hay líderes registrados")
        for member in ctx.guild.members:
            await self.assign_house(ctx, member, True)
            await self.save_state(ctx.guild.id)

    @commands.command("borrar_casas")
    @commands.has_permissions(administrator=True)
    async def remove_all(self, ctx):
        for house in self.houses[ctx.guild.id]:
            await house.delete()
        self.houses[ctx.guild.id].clear()
        await ctx.send("Se borraron todas las casas")
        await self.save_state(ctx.guild.id)

    async def create_all(self, ctx, leader):
        if leader in self.get_leaders(ctx):
            await ctx.send("¡Líder: {} ya tiene asignado casa!".format(leader.name))
            return
        role, leader_role = await self.create_roles(ctx, leader)
        print("Creados los roles")
        text_channel, voice_channel = await self.create_house_channels(ctx, role, leader_role, self.category[ctx.guild.id])

        return role, leader_role, text_channel, voice_channel

    async def create_house_channels(self, ctx, role, leader_role, category):
        permission_overwrites = {
            role: discord.PermissionOverwrite(read_messages=True),
            leader_role: discord.PermissionOverwrite(
                read_messages=True, manage_roles=True, manage_channels=True)
        }
        text_channel = await ctx.guild.create_text_channel(
            "casa-{}".format(role.name), overwrites=permission_overwrites, category=category, reason="Creación  de casa.")
        print("Creados los canales de texto")
        voice_channel = await ctx.guild.create_voice_channel(
            "casa-{}".format(role.name), overwrites=permission_overwrites, category=category, reason="Creación  de casa.")
        print("Creados los canales")

        return text_channel, voice_channel

    async def create_roles(self, ctx, leader):
        role_name = self.next_name if self.next_name else leader.name
        leader_role_name = "{}_lider".format(role_name)
        print("Creating roles for: {}".format(role_name))
        role = await ctx.guild.create_role(name=role_name)
        print("Created role")
        leader_role = await ctx.guild.create_role(name=leader_role_name)
        await leader.add_roles(leader_role, role, reason="Registro de lider a casa.")
        return role, leader_role

    def get_total(self, ctx):
        return sum([h.count for h in self.houses[ctx.guild.id]])

    async def assign_house(self, ctx, member, silent):
        # Check that we actually have roles to work with
        if len(self.houses[ctx.guild.id]) == 0:
            await ctx.send("¡No hay roles registrados!")
            return
        result = [house.role for house in self.houses[ctx.guild.id]
                  if house.role in member.roles]
        if len(result) > 0:
            await ctx.send("¡Ya fuiste asignado a una casa! {}".format(member.name))
            return

        total = self.get_total(ctx)
        previous = 0
        random_select = random.random()
        selected = random.choices(
            self.houses[ctx.guild.id], weights=[weights.ponder(total) for weights in self.houses[ctx.guild.id]], k=1)[0]
        selected.count += 1
        # We've already selected a house, but for dramatic purposes we delay it a little bit.
        if not silent:
            await ctx.send("Escogiendo el lugar adecuado para ti {}.".format(member.name))
        await asyncio.sleep(random.random()*1.8 + 0.2)
        await ctx.send("¡{} ,eres de la casa: {}!".format(member.name, selected.role.name))
        await member.add_roles(selected.role, reason="Registro a casa.")

    def get_leaders(self, ctx):
        return [house.leader for house in self.houses[ctx.guild.id]]

    def get_text_channels(self, ctx):
        return [house.text_channel for house in self.houses[ctx.guild.id]]

    def get_voice_channels(self, ctx):
        return [house.voice_channel for house in self.houses[ctx.guild.id]]

    async def house_from_ids(self, guild, role, leader_role, text_channel, voice_channel, leader,  count):

        r = guild.get_role(role)
        lr = guild.get_role(leader_role)
        tc = guild.get_channel(text_channel)
        vc = guild.get_channel(voice_channel)
        l = guild.get_member(leader)

        return House(r, lr, tc, vc, l, count)

    async def save_state(self, guild_id):
        self.persistence.save_data(
            guild_id,  self.category[guild_id].id, self.houses[guild_id])


class House:
    def __init__(self, role, leader_role, text_channel, voice_channel, leader, count=1):
        self.role = role
        self.leader_role = leader_role
        self.text_channel = text_channel
        self.voice_channel = voice_channel
        self.count = count
        self.leader = leader

    def ponder(self, maxCount):
        return self.count / maxCount

    def convert_id_dict(self):
        return {
            "role": self.role.id,
            "leader_role": self.leader_role.id,
            "leader": self.leader.id,
            "text_channel": self.text_channel.id,
            "voice_channel": self.voice_channel.id,
            "count": self.count
        }

    async def delete(self):
        await self.role.delete()
        await self.leader_role.delete()
        await self.voice_channel.delete()
        await self.text_channel.delete()

    async def change_name(self, name):
        if not name:  # cant have empty names
            return
        await self.role.edit(name="{}".format(name))
        await self.leader_role.edit(name="{}_leader".format(name))
        await self.voice_channel.edit(name="casa-{}".format(name))
        await self.text_channel.edit(name="casa-{}".format(name))
