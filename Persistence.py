import json


class Persistence:

    def __init__(self):
        pass

    def save_data(self, guild_id, category_id, houses):
        pass

    def load_data(self, guild_id):
        return None

    def get_data_file(self, guild_id):
        return None

    async def override_from_attachment(self, guiild_id, attachment):
        pass


class JsonPersistence(Persistence):

    def save_data(self, guild_id, category_id, houses):
        houses_id = [h.convert_id_dict() for h in houses]
        data = {
            "category": category_id,
            "houses": houses_id,
            "guild": guild_id
        }
        with open("discord_data_{}.json".format(guild_id), "w") as f:
            json.dump(data, f)

    def load_data(self, guild_id):
        try:
            with open("discord_data_{}.json".format(guild_id), "r") as f:
                data = json.load(f)
        except:
            return None, None, None

        category = None
        if "category" in data:
            category = data["category"]

        houses = None
        if "houses" in data:
            houses = data["houses"]

        guild = None
        if "guild" in data:
            guild = data["guild"]
        return guild, category, houses

    def get_data_file(self,  guild_id):
        return "discord_data_{}.json".format(guild_id)

    async def override_from_attachment(self, guiild_id, attachment):
        with open("discord_data_{}.json".format(guild_id), "w") as f:
            await attachment.save(f)
