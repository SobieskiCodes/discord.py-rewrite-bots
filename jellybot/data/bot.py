#-questions and leveling will be seperate cogs.
#-lock events/leaderboard channel to read only
#- Add the thing where you get an item every 5mins <- higher items have lower chance
#-Possibly add an admin only command to give/take items <- can override inv limit

from cogs.util import pyson
from discord.ext import commands
import asyncio
import discord
import os
import random


def is_owner():
    def predictate(ctx):
        if ctx.author is ctx.guild.owner:
            return True
        return False
    return commands.check(predictate)


class jellybot:
    def __init__(self, bot):
        self.bot = bot
        self.bot.items = pyson.Pyson('data/jellybot/items.json')

    async def on_guild_join(self, guild):
        if f'{str(guild.id)}.json' not in os.listdir("./data/jellybot/servers"):
            self.bot.newserver = pyson.Pyson(f'./data/jellybot/servers/{str(guild.id)}.json', {"users": {}})
            self.bot.newserver.save()

            self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(guild.id)}.json')
            for member in guild.members:
                if not member.bot:
                    if str(member.id) not in self.bot.server.data.get('users'):
                        new_user = {"itemlist": {}, "points": 0}
                        self.bot.server.data['users'][str(member.id)] = new_user
            self.bot.server.save()

        if not any(category.name == "jellybot" for category in guild.categories):
            try:
                create_category = await guild.create_category_channel("jellybot")
                contains = ['jelly-events', 'jelly-leaderboard', 'jelly-commands', 'jelly-questions']
                for channel_name in contains:
                    await guild.create_text_channel(channel_name, category=create_category)
                    await asyncio.sleep(1)
            except:
                await guild.owner.send('I am unable to create the channels I need, please create a category with the '
                                       'channels, "jelly-events, jelly-leaderboard, jelly-commands, jelly-questions"')

    async def on_member_join(self, member):
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(member.guild.id)}.json')
        if not member.bot:
            if str(member.id) not in self.bot.server.data.get('users'):
                new_user = {"itemlist": {}, "points": 0}
                self.bot.server.data['users'][str(member.id)] = new_user
                self.bot.server.save()

    @commands.is_owner()
    @commands.command(hidden=True)
    async def addpoints(self, ctx,  person: str=None, amount: str=None):
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.guild.id)}.json')
        if not person or not ctx.message.raw_mentions:
            await ctx.send('you forgot to include a person')
            return

        if not amount or not amount.isdigit():
            await ctx.send('invalid amount')
            return

        if str(ctx.message.raw_mentions[0]) in self.bot.server.data.get('users'):
            old_points = self.bot.server.data.get('users').get(str(ctx.message.raw_mentions[0])).get('points')
            self.bot.server.data['users'][str(ctx.message.raw_mentions[0])]['points'] = int(old_points) + int(amount)
            self.bot.server.save()
            await ctx.send('updated users points')
        else:
            await ctx.send('couldnt find that user')

    @commands.command()
    async def points(self, ctx, message: str = None):
        '''points shows current points
        '''
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.guild.id)}.json')

        if message is None:
            get_points = self.bot.server.data.get('users').get(str(ctx.author.id)).get('points')
            await ctx.send(f'{ctx.author.name} you have {get_points} points.')
            return

    async def remove_points(self, points, user,  ctx):
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.guild.id)}.json')
        old_points = self.bot.server.data.get('users').get(str(user)).get('points')
        self.bot.server.data['users'][str(user)]['points'] = int(old_points) - points
        self.bot.server.save()


    @commands.command()
    async def buy(self, ctx, message: str = None):
        '''buy [category] - choices are weak, skilled and frantic
        eg; buy weak
        '''
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.guild.id)}.json')
        events_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-events')
        item_list = ['weak', 'skilled', 'frantic']

        if message is None:
            await ctx.send('Categories are weak, skilled, and frantic.')
            return

        message = message.lower()

        weak_items = []
        skilled_items = []
        frantic_items = []
        for item in self.bot.items.data.get('items'):
            cost = self.bot.items.data.get('items').get(item).get('cost')
            if cost is 5:
                weak_items.append(item)
            if cost is 15:
                skilled_items.append(item)
            if cost is 30:
                frantic_items.append(item)
        if self.bot.server.data.get('users').get(str(ctx.author.id)).get('points') < cost:
            await ctx.send('you dont have enough points to buy that')
            return

        if message in item_list:
            weak_recieve = random.choice(weak_items)
            skilled_recieve = random.choice(skilled_items)
            frantic_recieve = random.choice(frantic_items)

            if message == 'weak':
                item_recieved = weak_recieve

            if message == 'skilled':
                item_recieved = skilled_recieve

            if message == 'frantic':
                item_recieved = frantic_recieve

            name = self.bot.items.data.get('items').get(item_recieved).get('name')

            player_inventory = self.bot.server.data.get('users').get(str(ctx.author.id)).get('itemlist')
            amount_to_add = []
            for item in player_inventory:
                get_amount = self.bot.server.data.get('users').get(str(ctx.author.id)).get('itemlist').get(item)
                amount_to_add.append(int(get_amount))

            if len(amount_to_add) == 0:
                self.bot.server.data['users'][(str(ctx.author.id))]['itemlist'][item_recieved] = 1
                self.bot.server.save()
                embed = discord.Embed(colour=discord.Colour(0xb2ff59),
                                      description=f'{ctx.message.author.name} you recieved {name}')
                await events_channel.send(embed=embed)
                await self.remove_points(cost, ctx.author.id, ctx)
                return

            else:
                total = 0
                for item in amount_to_add:
                    total = int(total) + int(item)

                if total >= 3:
                    embed = discord.Embed(colour=discord.Colour(0xb2ff59),
                                          description=f'{ctx.message.author.name} you have too many items already, '
                                                      f'please use one first.')
                    await events_channel.send(embed=embed)
                    return

                else:
                    get_player_inventory = self.bot.server.data.get('users').get((str(ctx.author.id))).get('itemlist')
                    if item_recieved in get_player_inventory:
                        get_current_amount = self.bot.server.data.get('users').get((str(ctx.author.id))).get('itemlist').get(
                            item_recieved)
                        new_value = get_current_amount + 1
                        self.bot.server.data['users'][(str(ctx.author.id))]['itemlist'][item_recieved] = new_value
                        self.bot.server.save()
                        embed = discord.Embed(colour=discord.Colour(0xb2ff59),
                                              description=f'{ctx.message.author.name} you recieved {name}')
                        await events_channel.send(embed=embed)
                        await self.remove_points(cost, ctx.author.id, ctx)
                        return

                    else:
                        self.bot.server.data['users'][(str(ctx.author.id))]['itemlist'][item_recieved] = 1
                        self.bot.server.save()
                        embed = discord.Embed(colour=discord.Colour(0xb2ff59),
                                              description=f'{ctx.message.author.name} you recieved {name}')
                        await events_channel.send(embed=embed)
                        await self.remove_points(cost, ctx.author.id, ctx)
                        return

        else:
            await ctx.send('item categories are weak, skilled and frantic.')
            return

    @commands.command()
    async def store(self, ctx):
        '''store shows all buyable items'''
        get_items = self.bot.items.data.get('items')
        embed = discord.Embed(title="Store", description=ctx.message.author.mention,
                              colour=discord.Colour(0x278d89))

        itemsort = sorted(get_items, key=lambda x: get_items[x]['cost'], reverse=False)
        items = ''
        descriptions = ''
        for item in itemsort:
            description = self.bot.items.data.get('items').get(item).get('description')
            category = self.bot.items.data.get('items').get(item).get('group')
            items += f'{item} ({category})\n'
            descriptions += f'{description}\n'

        embed.add_field(name='Item & category', value=items)
        embed.add_field(name='Description', value=descriptions)
        await ctx.send(embed=embed)

    @commands.command()
    async def pos(self, ctx, message: str = None):
        '''pos [user]
        user is optional - shows players or users position.
        '''
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.guild.id)}.json')
        users = self.bot.server.data.get('users')
        events_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-events')
        if message is None:
            author = ctx.message.author
            leaderboard = sorted(users, key=lambda x: users[x]['points'], reverse=True)
            position = leaderboard.index(str(author.id))
            embed = discord.Embed(colour=discord.Colour(0x8e24aa),
                                  description=f'{ctx.message.author.name} you are in position {position+1}')
            await events_channel.send(embed=embed)
            return

        elif not ctx.message.raw_mentions:
            await ctx.send('no mentions')
            return
        else:
            user = ctx.channel.guild.get_member(ctx.message.raw_mentions[0])
            leaderboard = sorted(users, key=lambda x: users[x]['points'], reverse=True)
            position = leaderboard.index(str(ctx.message.raw_mentions[0]))
            embed = discord.Embed(colour=discord.Colour(0x8e24aa), description=f'{user.name} is in position {position}')
            await events_channel.send(embed=embed)

    @commands.command()
    async def inventory(self, ctx, message: str = None):
        '''Inventory [user]
        user is optional - shows players or users inventory.
        '''
        events_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-events')
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.guild.id)}.json')
        if message is None:
            try:
                get_inventory = self.bot.server.data.get('users').get(str(ctx.message.author.id)).get('itemlist')
                embed = discord.Embed(title="Inventory", description=ctx.message.author.name,
                                      colour=discord.Colour(0xffeb3b))
                descriptions = ''
                items = ''
                for item in get_inventory:
                    name = self.bot.items.data.get('items').get(item).get('name')
                    description = self.bot.items.data.get('items').get(item).get('description')
                    itemamount = self.bot.server.data.get('users').get(str(ctx.message.author.id)).get('itemlist').get(item)
                    descriptions += f'{description}\n'
                    items += f'{name} x({itemamount})\n'

                embed.add_field(name='Item & Amount', value=items)
                embed.add_field(name='Description', value=descriptions)
                await events_channel.send(embed=embed)
                return
            except:
                embed = discord.Embed(title="Inventory", description=ctx.message.author.name,
                                      colour=discord.Colour(0xffeb3b))
                embed.add_field(name='Item & Amount', value="None")
                embed.add_field(name='Description', value='None')
                await events_channel.send(embed=embed)
                return

        if not ctx.message.raw_mentions:
            await ctx.send('no mentions')
            return

        else:
            try:
                user = ctx.channel.guild.get_member(ctx.message.raw_mentions[0])
                get_inventory = self.bot.server.data.get('users').get(str(ctx.message.raw_mentions[0])).get('itemlist')
                embed = discord.Embed(title="Inventory", description=f'{user.name}', colour=discord.Colour(0xffeb3b))
                descriptions = ''
                items = ''
                for item in get_inventory:
                    name = self.bot.items.data.get('items').get(item).get('name')
                    description = self.bot.items.data.get('items').get(item).get('description')
                    itemamount = self.bot.items.data.get('users').get(str(ctx.message.raw_mentions[0])).get('itemlist').get(item)
                    descriptions += f'{description}\n'
                    items += f'{name} x({itemamount})\n'

                embed.add_field(name='Item & Amount', value=items)
                embed.add_field(name='Description', value=descriptions)
                await events_channel.send(embed=embed)
                return

            except:
                embed = discord.Embed(title="Inventory", description=f'{user.name}', colour=discord.Colour(0xffeb3b))
                embed.add_field(name='Item & Amount', value="None")
                embed.add_field(name='Description', value='None')
                await events_channel.send(embed=embed)

    async def item_timer(self, player, emoji, ctx):
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.message.guild.id)}.json')
        counter = 0
        while True:
            user_list = []
            for user in self.bot.server.data.get('users'):
                user_list.append(user)

            randomperson = random.choice(user_list)
            if randomperson == player:
                while randomperson == player:
                    randomperson = random.choice(user_list)

            events_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-events')
            counter = counter + 1
            points = self.bot.server.data.get('users').get(randomperson).get('points')
            value = self.bot.items.data.get('items').get(emoji).get('value')
            new_points = points + value
            if new_points <= 0:
                new_points = 0
            self.bot.server.data['users'][randomperson]['points'] = int(new_points)
            self.bot.server.save()
            player = await self.bot.get_user_info(int(randomperson))
            embed = discord.Embed(colour=discord.Colour(0xc62828),
                                  description=f'<@{player}> '
                                              f'used <{emoji}> on {player.name}, they now have {new_points} points!')
            await events_channel.send(embed=embed)

            if counter == 10:
                break
            else:
                await  asyncio.sleep(180)

    async def remove_item(self, player, item, amount, ctx):
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.message.guild.id)}.json')
        new_amount = amount - 1
        self.bot.server.data['users'][str(player)]['itemlist'][item] = int(new_amount)
        if new_amount == 0:
            self.bot.server.data['users'][str(player)]['itemlist'].pop(item, None)
        self.bot.server.save()

    @commands.command()
    async def use(self, ctx, emoji: discord.Emoji):
        '''use <item>
        use any item from with the store.
        '''
        events_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-events')
        self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.message.guild.id)}.json')
        users = self.bot.server.data.get('users')

        itemlist = self.bot.items.data.get('items')

        if isinstance(emoji, discord.Emoji):
            emoji = emoji.name

        list_items = []
        for item in itemlist:
            list_items.append(item)

        if emoji not in list_items:
            await ctx.send('Thats not an item')
            return

        if emoji is None:
            await ctx.send('you didn\'t try to use anything')
            return

        if emoji in list_items:
            above = self.bot.items.data.get('items').get(emoji).get('above')
            below = self.bot.items.data.get('items').get(emoji).get('below')
            cost = self.bot.items.data.get('items').get(emoji).get('cost')
            target = self.bot.items.data.get('items').get(emoji).get('target')
            value = self.bot.items.data.get('items').get(emoji).get('value')
            amount = self.bot.server.data.get('users').get(str(ctx.message.author.id)).get('itemlist').get(emoji)
            description = self.bot.items.data.get('items').get(emoji).get('description')

            if amount == 0 or amount is None:
                await ctx.send(f'you have no {emoji} to use')
                return

            if cost is 5:
                embed = discord.Embed(colour=discord.Colour(0x00bcd4),
                                      description=f'{ctx.message.author.name} used {emoji} : "{description}"')
                await events_channel.send(embed=embed)
            if cost is 15:
                embed = discord.Embed(colour=discord.Colour(0x1976d2),
                                      description=f'{ctx.message.author.name} used {emoji} : "{description}"')
                await events_channel.send(embed=embed)
            if cost is 30:
                embed = discord.Embed(colour=discord.Colour(0x1a237e),
                                      description=f'{ctx.message.author.name} used {emoji} : "{description}"')
                await events_channel.send(embed=embed)

            leaderboard = sorted(users, key=lambda x: users[x]['points'], reverse=True)
            position = leaderboard.index((str(ctx.message.author.id)))
            get_emoji = discord.utils.get(self.bot.emojis, name=emoji)
            if target is None:
                if above is True:
                    if position is 0:
                        await ctx.send(f'You are in position {position+1}, you can\'t use this item')
                        return

                    else:
                        points_above = self.bot.server.data.get('users').get(leaderboard[position - 1]).get('points')
                        new_points_above = int(points_above) + int(value)
                        if new_points_above <= 0:
                            new_points_above = int(0)
                        self.bot.server.data['users'][leaderboard[position - 1]]['points'] = int(new_points_above)
                        self.bot.server.save()
                        embed = discord.Embed(colour=discord.Colour(0xc62828),
                                              description=f'{ctx.message.author.name}\'s {get_emoji} just hit '
                                                          f'<@{leaderboard[position-1]}>! They now have {new_points_above} points!')
                        await events_channel.send(embed=embed)
                await self.remove_item(ctx.message.author.id, emoji, amount, ctx)

                if below is True:
                    if position + 1 == len(users):
                        await ctx.send(f'You are in position {position+1}(last place) you can\'t use this item')
                        return

                    else:
                        points_below = self.bot.server.data.get('users').get(leaderboard[position + 1]).get('points')
                        new_points_below = int(points_below) + int(value)
                        if new_points_below <= 0:
                            new_points_below = int(0)
                        self.bot.server.data['users'][leaderboard[position + 1]]['points'] = int(new_points_below)
                        self.bot.server.save()
                        embed = discord.Embed(colour=discord.Colour(0xc62828),
                                              description=f'{ctx.message.author.name}\'s {get_emoji} just hit '
                                                          f'<@{leaderboard[position+1]}>! They now have {new_points_below} points!')
                        await events_channel.send(embed=embed)
                        return

            if target is not None:
                if target == "random":
                    if emoji == "ink":
                        await self.item_timer(ctx.message.author.id, emoji, ctx)
                        await self.remove_item(ctx.message.author.id, emoji, amount, ctx)
                        return

                    if emoji == "sprinkler":
                        await self.item_timer(ctx.message.author.id, emoji, ctx)
                        await self.remove_item(ctx.message.author.id, emoji, amount, ctx)
                        return

                    if emoji == "boo":
                        await self.item_timer(ctx.message.author.id, emoji, ctx)
                        return

                    else:
                        leaderboard = sorted(users, key=lambda x: users[x]['points'], reverse=True)
                        pick_random_user = random.choice(leaderboard)

                        if pick_random_user == ctx.message.author.id:
                            while pick_random_user == ctx.message.author.id:
                                pick_random_user = random.choice(leaderboard)

                        points_old = self.bot.server.data.get('users').get(pick_random_user).get('points')
                        new_points_random = int(points_old) + int(value)

                        if new_points_random <= 0:
                            new_points_random = int(0)
                        self.bot.server.data['users'][pick_random_user]['points'] = int(new_points_random)
                        self.bot.server.save()
                        embed = discord.Embed(colour=discord.Colour(0xc62828),
                                              description=f'{ctx.message.author.name}\'s {get_emoji} hit '
                                                          f'<@{pick_random_user}>! They now have {new_points_random} points!')
                        await events_channel.send(embed=embed)
                        await self.remove_item(ctx.message.author.id, emoji, amount, ctx)
                        return

                if target == "all":
                    await ctx.send(f'target is {value} {target}')
                    return

                if target == "self":
                    points_old_self = self.bot.server.data.get('users').get(str(ctx.message.author.id)).get('points')
                    value = self.bot.items.data.get('items').get(emoji).get('value')
                    new_points_self = points_old_self + value
                    self.bot.server.data['users'][str(ctx.message.author.id)]['points'] = int(new_points_self)
                    self.bot.server.save()
                    embed = discord.Embed(colour=discord.Colour(0xc62828),
                                          description=f'{ctx.message.author.name}\'s used {get_emoji} and gained '
                                                      f'{value} points, for a total of {new_points_self} points.')
                    await events_channel.send(embed=embed)
                    await self.remove_item(ctx.message.author.id, emoji, amount, ctx)
                    return

                if target == "steal":
                    user_list = []
                    for user in users:
                        user_list.append(user)

                    target = None
                    while not target:
                        target = random.choice(user_list)
                        items = self.bot.server.data.get('users').get(target).get('itemlist')
                        if target == ctx.message.author.id:
                            target = None
                        if len(items) == 0:
                            target = None

                    item_list = []
                    targets_items = self.bot.server.data.get('users').get(target).get('itemlist')
                    for item in targets_items:
                        item_list.append(item)
                    item_to_steal = random.choice(item_list)

                    amount_item_target = self.bot.server.data.get('users').get(target).get('itemlist').get(item_to_steal)
                    new_amount_item_target = amount_item_target - 1
                    if new_amount_item_target == 0:
                        self.bot.server.data['users'][target]['itemlist'].pop(item_to_steal, None)
                    self.bot.server.save()
                    player_items = self.bot.server.data.get('users').get(ctx.message.author.id).get('itemlist')
                    player_items_list = []
                    for item in player_items:
                        player_items_list.append(item)

                    if item_to_steal in player_items_list:
                        amount = self.bot.server.data.get('users').get(ctx.message.author.id).get('itemlist').get(item_to_steal)
                        new_amount = amount + 1
                        self.bot.server.data['users'][ctx.message.author.id]['itemlist'][item_to_steal] = new_amount
                    self.bot.server.save()

                    if item_to_steal not in player_items_list:
                        self.bot.server.data['users'][ctx.message.author.id]['itemlist'][item_to_steal] = 1
                    self.bot.server.save()

                    value = self.bot.items.data.get('items').get(emoji).get('value')
                    if value > 0:
                        get_points = self.bot.server.data.get('users').get(ctx.message.author.id).get('points')
                        new_points = get_points + value
                        self.bot.server.data['users'][ctx.message.author.id]['points'] = new_points
                    self.bot.server.save()
                    await self.remove_item(ctx.message.author.id, emoji, amount, ctx)
                    name = self.bot.server.data.get('items').get(item_to_steal).get('name')
                    embed = discord.Embed(colour=discord.Colour(0xc62828),
                                          description=f'{ctx.message.author.name}\'s {get_emoji} hit '
                                                      f'<@{target}> and stole {name}!')
                    await events_channel.send(embed=embed)

                if target == "targeted":
                    mention_list = []
                    for mention in ctx.message.mentions:
                        mention_list.append(mention.id)

                    if len(mention_list) < 1:
                        await ctx.send('you need to include a mention')
                        return

                    if len(mention_list) >= 2:
                        await ctx.send('you should include only one mention')
                        return

                    if mention_list[0] == ctx.message.author.id:
                        await ctx.send('you cant use it on yourself....')
                        return

                    if len(mention_list) == 1:
                        await self.remove_item(ctx.message.author.id, emoji, amount, ctx)
                        target = mention_list[0]
                        points_old = self.bot.server.data.get('users').get(target).get('points')
                        new_points_target = int(points_old) + int(value)
                        if new_points_target <= 0:
                            new_points_target = int(0)
                        self.bot.server.data['users'][target]['points'] = int(new_points_target)
                        self.bot.server.save()
                        embed = discord.Embed(colour=discord.Colour(0xc62828),
                                              description=f'{ctx.message.author.name}\'s {get_emoji} just hit <@{target}>!'
                                                          f' They now have {new_points_target} points!')
                        await events_channel.send(embed=embed)
                        return

                if target == "top":
                    if position == 0:
                        await ctx.send('you cant use this, you are in first')
                        return
                    await self.remove_item(ctx.message.author.id, emoji, amount, ctx)
                    leaderboard = sorted(users, key=lambda x: users[x]['points'], reverse=True)
                    points_old = self.bot.server.data.get('users').get(leaderboard[0]).get('points')
                    new_points = points_old + value
                    self.bot.server.data['users'][leaderboard[0]]['points'] = int(new_points)
                    self.bot.server.save()
                    embed = discord.Embed(colour=discord.Colour(0xc62828),
                                          description=f'{ctx.message.author.name}\'s {get_emoji} just hit '
                                                      f'<@{leaderboard[0]}>! They now have {new_points} points!')
                    await events_channel.send(embed=embed)
                    return
        else:
            await ctx.send('shrug')
            return

    @commands.command()
    @is_owner()
    async def starttop10(self, ctx):
        '''starttop10 - owner only - starts the leaderboard channel
        this does not stop on its own
        '''
        await ctx.send('starting..')
        await self.leaderboard(ctx)


    @commands.command()
    @is_owner()
    async def jellygiveaway(self, ctx):
        '''jellygiveaway - owner only - starts the giveaway
        this does not stop on its own
        '''
        await ctx.send('starting..')
        await self.giveaway(ctx)

    async def giveaway(self, ctx):
        while True:
            await asyncio.sleep(600)
            self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.message.guild.id)}.json')
            self.users = self.bot.server.data.get('users')
            pickone = random.choice(list(self.users))
            events_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-events')
            user_old_points = self.bot.server.data.get('users').get(pickone).get('points')
            new_points = user_old_points + 10
            self.bot.server.data['users'][pickone]['points'] = int(new_points)
            self.bot.server.save()
            player = await self.bot.get_user_info(int(pickone))
            embed = discord.Embed(colour=discord.Colour(0x7cb342),
                                  description=f'{player.name} just recieved 10 points from the giveaway and now has '
                                              f'{new_points} points!')
            await events_channel.send(embed=embed)

    async def leaderboard(self, ctx):
        l_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-leaderboard')
        while True:
            async for message in l_channel.history():
                await message.delete()
            async with l_channel.typing():
                self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.message.guild.id)}.json')
                self.users = self.bot.server.data.get('users')
                leaderboard = sorted(self.users, key=lambda x: self.users[x]['points'], reverse=True)
                leaderboard = list(enumerate(leaderboard))
                embed = discord.Embed(colour=discord.Colour(0x278d89))
                embed.set_thumbnail(url='https://cgg.website/lb.png')
                players_list = ''
                points_list = ''
                for place, entry in leaderboard[:10]:
                    user_points = self.users[entry]['points']
                    player = await self.bot.get_user_info(entry)
                    players_list += f'**#{place+1}** {player.name}\n'
                    points_list += f'{user_points}\n'

                embed.add_field(name='Players', value=players_list)
                embed.add_field(name='Points', value=points_list)
            await l_channel.send(embed=embed)
            await asyncio.sleep(1800)


def setup(bot):
    bot.add_cog(jellybot(bot))
