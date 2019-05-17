from cogs.util import pyson
from discord.ext import commands
import discord
import asyncio
import random


def is_owner():
    def predictate(ctx):
        if ctx.author is ctx.guild.owner:
            return True
        return False
    return commands.check(predictate)


class qanda:
    def __init__(self, bot):
        self.bot = bot
        self.bot.qa = pyson.Pyson('data/jellybot/qa.json')
        self.timer = True

    async def set_timer(self):
        await asyncio.sleep(30)
        self.timer = False

    @is_owner()
    @commands.command()
    async def startqchannel(self, ctx):
        await ctx.send('starting..')
        await self.start_q_channel(ctx)

    async def purge_channel(self, ctx, time: int=240):
        q_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-questions')
        await q_channel.send('Channel will be purged in 4m.')
        await asyncio.sleep(time)
        async for message in q_channel.history():
            await message.delete()
        return

    async def start_q_channel(self, ctx):
        while self.timer:
            q_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-questions')
            events_channel = discord.utils.get(ctx.message.guild.channels, name='jelly-events',)
            self.bot.server = pyson.Pyson(f'data/jellybot/servers/{str(ctx.guild.id)}.json')
            question_list = []
            for question in self.bot.qa.data.get('questions'):
                question_list.append(question)
            pick_question = random.choice(question_list)
            question = self.bot.qa.data.get('questions').get(pick_question).get('question')
            answer = self.bot.qa.data.get('questions').get(pick_question).get('answer')
            await q_channel.send(f'Question time! \n```{question}```')
            guess = None
            self.bot.loop.create_task(self.set_timer())

            def q_channel_check(m):
                return m.channel.name == 'jelly-questions'

            while not guess and self.timer:
                guess_msg = await self.bot.wait_for('message', check=q_channel_check, timeout=30)
                if guess_msg:
                    guess = guess_msg.content.lower()
                    if guess == answer:
                        user_points = self.bot.server.data.get('users').get(str(guess_msg.author.id)).get('points')
                        new_points = user_points + 10
                        self.bot.server.data['users'][str(guess_msg.author.id)]['points'] = int(new_points)
                        self.bot.server.save()
                        embed = discord.Embed(colour=discord.Colour(0x06f116),
                                              description=f'{guess_msg.author.mention},'
                                                          f'you have guessed correctly and earned 10 points, for a total of {new_points}!')
                        await q_channel.send(embed=embed)

                        event = discord.Embed(colour=discord.Colour(0x06f116), description=f'{guess_msg.author.mention}'
                                                                                           f' has answered "{question}" '
                                                                                           f'correctly and earned 10 points, they now have {new_points} points!')
                        await events_channel.send(embed=event)
                        await self.purge_channel(ctx)
                    else:
                        guess = None
            if not guess:
                embed = discord.Embed(colour=discord.Colour(0xf20707),
                                      description=f'Nobody got the question correct!')
                await q_channel.send(embed=embed)
                await self.purge_channel(ctx)

            await asyncio.sleep(1500)


def setup(bot):
    bot.add_cog(qanda(bot))
