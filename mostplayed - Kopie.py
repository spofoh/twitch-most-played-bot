import os
import json
import requests
from twitchio.ext import commands
import asyncio
from dotenv import load_dotenv

load_dotenv()

class Bot(commands.Bot):

    def __init__(self):
        if not os.path.exists('channels.json'):
            with open('channels.json', 'w') as f:
                json.dump(["CHANNEL"], f)
        with open('channels.json', 'r') as f:
            channels = json.load(f)
        super().__init__(token=os.getenv('TOKEN'), client_id=os.getenv('CLIENT_ID'), prefix=os.getenv('PREFIX'),
                         initial_channels=channels)

    async def event_ready(self):
        print(f'Ready | {self.nick}')

    async def event_message(self, message):
        if message.echo:
            return
        await self.handle_commands(message)

    async def event_command_error(self, ctx, error: Exception) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            print(error)
            return
        
    @commands.command(name='join')
    async def join(self, ctx, channel: str):
        if ctx.author.name.lower() == os.getenv('USERNAME').lower():
            with open('channels.json', 'r') as f:
                channels = json.load(f)
            if channel not in channels:
                channels.append(channel)
                with open('channels.json', 'w') as f:
                    json.dump(channels, f)
                await self.join_channels([channel])
                await ctx.reply(f"Joined the channel: {channel}")
            else:
                await ctx.reply(f"I have already joined the channe {channel}.")

    @commands.command(name='leave')
    async def leave(self, ctx, channel: str):
        if ctx.author.name.lower() == os.getenv('USERNAME').lower():
            with open('channels.json', 'r') as f:
                channels = json.load(f)
            if channel in channels:
                channels.remove(channel)
                with open('channels.json', 'w') as f:
                    json.dump(channels, f)
                await self.part_channels([channel])
                await ctx.reply(f"Left the channel: {channel}")
            else:
                await ctx.reply(f"I'm not joined the channel.")

    @commands.command(name='mostplayed')
    @commands.cooldown(rate=1, per=15, bucket=commands.Bucket.channel)
    async def my_command(self, ctx, streamer_name: str, num_games: int):
        if num_games > 10:
            num_games = 10
        elif num_games < 1:
            num_games = 1

        url = f"https://sullygnome.com/api/standardsearch/{streamer_name}/false/true/false/false"
        response = requests.get(url)
        data = response.json()
        if not data:
            await ctx.reply("/me ⚠️The searched streamer was not found!⚠️")
            return
        
        streamer_id = data[0]['value']
        safe_streamer_name = data[0]['displaytext']

        url = f"https://sullygnome.com/api/tables/channeltables/games/365/{streamer_id}/%20/1/2/desc/0/100"
        response = requests.get(url)
        data = response.json()
        
        if not data['data']:
            await ctx.reply(f"/me ⚠️{safe_streamer_name} has not played a game yet or is not being tracked yet.⚠️")
            return

        num_games = min(num_games, len(data['data']))
        messages = []
        current_message = f"{safe_streamer_name}: "
        for i in range(num_games):
            game = data['data'][i]
            game_name = game['gamesplayed'].split('|')[0]
            if '.' in game_name:
                game_name = game_name.replace('.', '(.)')
            stream_time = round(game['streamtime'] / 60, 1)
            total_stream_time = game['channelstreamtime'] / 60
            percentage = round((stream_time / total_stream_time) * 100, 1)

            if stream_time.is_integer():
                stream_time = int(stream_time)
            if percentage.is_integer():
                percentage = int(percentage)

            new_line = f"{i+1}. {stream_time} Stunden ({percentage}%) {game_name}"
            if len(current_message + new_line + " | ") > 500:
                messages.append(current_message.rstrip(" | "))
                current_message = new_line + " | "
            else:
                current_message += new_line + " | "

        messages.append(current_message.rstrip(" | "))

        for message in messages:
            await ctx.reply('/me ' + message)
            await asyncio.sleep(0.5)


bot = Bot()
bot.run()
