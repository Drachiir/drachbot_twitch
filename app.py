import json
import asyncio
import aiohttp
from twitchio.ext import commands

recc_values = [
    150,
    150,
    215,
    270,
    335,
    445,
    570,
    700,
    820,
    1075,
    1360,
    1560,
    1880,
    2200,
    2770,
    3350,
    3930,
    4700,
    5900,
    7100,
    8500
]

def check_command_enabled(command_list, command):
    if command not in command_list:
        return True
    else:
        return False
    
with open("Files/json/Secrets.json", "r") as f:
    secret = json.load(f)
    f.close()

with open("Files/json/streamers.json", "r") as f:
    streamer_dict = json.load(f)
    f.close()

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=secret["twitchbot"], prefix='!', initial_channels=list(streamer_dict.keys()))
        self.session = None
        
    async def event_ready(self):
        self.session = aiohttp.ClientSession(headers={'x-api-key': secret.get('apikey')})
        print(f'Logged in as {self.nick}')
    
    async def event_message(self, message):
        if message.echo:
            return
        await self.handle_commands(message)

    @commands.command()
    async def elo(self, ctx: commands.Context):
        if not check_command_enabled(streamer_dict[ctx.channel.name][1], "elo"):
            return
        playername: str = ctx.message.content[5:]
        try:
            if playername[-1].encode("unicode_escape") == b'\\U000e0000':
                playername = playername[:-2]
        except IndexError:
            pass
        if playername == "":
            playername = streamer_dict[ctx.channel.name][0]
        #check if player in top X
        url = f'https://apiv2.legiontd2.com/players/stats?limit={200}&sortBy=overallElo&sortDirection=-1'
        async with self.session.get(url) as response:
            if response.status != 200:
                await ctx.reply(f"Bot error 😭")
                return
            leaderboard = json.loads(await response.text())
        for i, player in enumerate(leaderboard):
            if player["profile"][0]["playerName"].casefold() == playername.casefold():
                playername = player["profile"][0]["playerName"]
                stats = player
                rank = i+1
                break
        else:
            #pull data manually if not in top X
            request_type = 'players/byName/'
            url = 'https://apiv2.legiontd2.com/' + request_type + playername
            async with self.session.get(url) as response:
                if response.status != 200:
                    await ctx.reply(f"{playername} not found")
                    return
                playerprofile = json.loads(await response.text())
                playername = playerprofile["playerName"]
            request_type = 'players/stats/'
            url = 'https://apiv2.legiontd2.com/' + request_type + playerprofile["_id"]
            async with self.session.get(url) as response:
                if response.status != 200:
                    await ctx.reply(f"Bot error 😭")
                    return
                rank = None
                stats = json.loads(await response.text())
        if rank:
            start_string = f"is Rank {rank},"
        else:
            start_string = "is"
        match playername.casefold():
            case "fine":
                end_string = " 🍆"
            case "pennywise":
                end_string = "🤡"
            case _:
                end_string = ""
        try:
            await ctx.reply(f"{playername} {start_string} {stats["overallElo"]} Elo{end_string}")
        except Exception:
            await ctx.reply(f"No data available for {playername}")
    
    @commands.command()
    async def rank(self, ctx: commands.Context):
        if not check_command_enabled(streamer_dict[ctx.channel.name][1], "rank"):
            return
        rank = ctx.message.content[6:]
        try:
            if rank[-1].encode("unicode_escape") == b'\\U000e0000':
                rank = rank[:-2]
            rank = int(rank)
        except Exception:
            await ctx.reply("Need a number e.g !rank 1")
            return
        if rank < 1:
            if "shadowings" in ctx.author.display_name:
                await ctx.reply(f"Bad shadow Madge")
            else:
                await ctx.reply(f"Need a number greater than 0")
            return
        url = f'https://apiv2.legiontd2.com/players/stats?limit={1}&offset={rank-1}&sortBy=overallElo&sortDirection=-1'
        async with self.session.get(url) as response:
            if response.status != 200:
                await ctx.reply(f"Bot error 😭")
                return
            try:
                stats = json.loads(await response.text())[0]
            except IndexError:
                await ctx.reply(f"Bot error 😭")
                return
        
        await ctx.reply(f"{stats["profile"][0]["playerName"]} is Rank {rank}, {stats["overallElo"]} Elo")
    
    @commands.command()
    async def lobby(self, ctx: commands.Context):
        if not check_command_enabled(streamer_dict[ctx.channel.name][1], "lobby"):
            return
        name = ctx.message.content[7:]
        try:
            if name[-1].encode("unicode_escape") == b'\\U000e0000':
                name = name[:-2]
        except IndexError:
            pass
        if not name:
            name = streamer_dict[ctx.channel.name][0]
        url = f'https://stats.drachbot.site/api/livegames/{name}'
        async with self.session.get(url) as response:
            if response.status != 200:
                print(response.status)
                await ctx.reply(f"Bot error 😭")
                return
            try:
                game = json.loads(await response.text())
            except IndexError:
                await ctx.reply(f"Bot error 😭")
                return
        if not game:
            await ctx.reply(f"{name} is not in game currently.")
            return
        await ctx.reply((", ".join([f"{player[0]}: {player[1]}" for player in game[2]]) + " vs. " + (", ".join([f"{player[0]}: {player[1]}" for player in game[3]]))))
    
    @commands.command()
    async def sellout(self, ctx: commands.Context):
        if not check_command_enabled(streamer_dict[ctx.channel.name][1], "sellout"):
            return
        name = ctx.message.content[9:]
        try:
            if name[-1].encode("unicode_escape") == b'\\U000e0000':
                name = name[:-2]
        except IndexError:
            pass
        if not name:
            name = streamer_dict[ctx.channel.name][0]
        url = f'https://stats.drachbot.site/api/livegames/{name}'
        async with self.session.get(url) as response:
            if response.status != 200:
                print(response.status)
                await ctx.reply(f"Bot error 😭")
                return
            try:
                game = json.loads(await response.text())
            except IndexError:
                await ctx.reply(f"Bot error 😭")
                return
        if not game:
            await ctx.reply(f"{name} is not in game currently.")
            return
        team_one = game[2]
        team_two = game[3]
        you = None
        teammate = None
        opponent = None
        other = None

        if team_one[0][0] == name:  # P1
            you = int(team_one[0][1])
            teammate = int(team_one[1][1])  # P2
            opponent = int(team_two[0][1])  # P3 (sending target)
            other = int(team_two[1][1])  # P4
        elif team_one[1][0] == name:  # P2
            you = int(team_one[1][1])
            teammate = int(team_one[0][1])  # P1
            opponent = int(team_two[1][1])  # P4 (sending target)
            other = int(team_two[0][1])  # P3
        elif team_two[0][0] == name:  # P3
            you = int(team_two[0][1])
            teammate = int(team_two[1][1])  # P4
            opponent = int(team_one[1][1])  # P2 (sending target)
            other = int(team_one[0][1])  # P1
        elif team_two[1][0] == name:  # P4
            you = int(team_two[1][1])
            teammate = int(team_two[0][1])  # P3
            opponent = int(team_one[0][1])  # P1 (sending target)
            other = int(team_one[1][1])  # P2
        else:
            await ctx.reply(f"Could not find your name in the game.")
            return
        
        sellout_score = you + other - teammate - opponent
        if sellout_score > 0:
            recommendation = "You should sell out your teammate."
        else:
            recommendation = "You should not sell out your teammate."
        
        await ctx.reply(f"Sellout Score for {name}: {sellout_score}. {recommendation}")
    
    @commands.command()
    async def info(self, ctx: commands.Context):
        if not check_command_enabled(streamer_dict[ctx.channel.name][1], "info"):
            return
        wave = ctx.message.content[6:]
        try:
            if wave[-1].encode("unicode_escape") == b'\\U000e0000':
                wave = wave[:-2]
            wave = int(wave)
            if 1 > wave > 21:
                await ctx.reply("Need a number 1-21")
        except Exception:
            await ctx.reply("Need a number 1-21")
            return
        await ctx.reply(f"Wave {wave} recc. value is {recc_values[wave-1]}")

if __name__ == "__main__":
    bot = Bot()
    bot.run()