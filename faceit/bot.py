import discord
from discord.ext import commands
import aiohttp
import jthon


bot = commands.Bot(command_prefix='?', )
token = 'DISCORD_TOKEN_HERE'
headers = {"Accept": "application/json", "Authorization": "Bearer FACEIT_API_TOKEN_HERE"}
users = jthon.load('users')
base = "https://open.faceit.com/data/v4/players?nickname="
rank_up_dict = {
    'levels': {
        '1': 800,
        '2': 801,
        '3': 951,
        '4': 1101,
        '5': 1251,
        '6': 1401,
        '7': 1551,
        '8': 1701,
        '9': 1851,
        '10': 2001
    }
}


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def add(ctx, user: str=None):
    """add yoself"""
    async with bot.aiohttp.get(f"{base}{user}", headers=headers) as resp:
        if resp.status == 200:
            users['users'][ctx.author.id] = user
            users.save()
            await ctx.send(f"{ctx.author.mention} you've been added to the db with {user}")
        else:
            await ctx.send("Seems that user doesn't exist")

@bot.command()
async def profile(ctx, user: str=None):
    if not user:
        user = users.get('users').get(str(ctx.author.id))
        async with bot.aiohttp.get(f"{base}{user}", headers=headers) as resp:
            if resp.status == 200:
                e = discord.Embed(title='Faceit Profile', colour=discord.Colour(0x278d89), )
                load_response_into_jthon = jthon.load('data', await resp.json())
                avatar = load_response_into_jthon.get("avatar")
                get_elo = load_response_into_jthon.get("games").get("csgo").get("faceit_elo")
                get_skill_level = load_response_into_jthon.get("games").get("csgo").get("skill_level")
                e.set_thumbnail(url=avatar)
                e.add_field(name='Elo', value=get_elo, inline=False)
                e.add_field(name='Skill Level', value=get_skill_level, inline=True)
                if get_skill_level.data < 10:
                    next_level = rank_up_dict.get('levels').get(str(get_skill_level.data + 1))
                    tnl = next_level - get_elo.data
                e.add_field(name='Elo TNL', value=str(tnl), inline=False)
                e.set_footer(text=f"https://www.faceit.com/en/players/{user}")
                await ctx.send(embed=e)

    else:
        print('user provided')


async def create_aiohttp():
    bot.aiohttp = aiohttp.ClientSession()


bot.loop.create_task(create_aiohttp())
bot.run(token)
