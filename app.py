import json
import asyncio
import traceback

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

def calculate_win_probability(team_a_elo, team_b_elo):
    return 1 / (1 + 10 ** ((team_b_elo - team_a_elo) / 400))

def calculate_elo_change(team_elo, opponent_elo):
    K = 32
    win_prob = calculate_win_probability(team_elo, opponent_elo)
    elo_change = K * (1 - win_prob)  # result = 1 for win
    elo_change = min(30, max(-30, elo_change))
    if elo_change < 2:
        elo_change = 2
    return round(elo_change)
    
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
    async def help(self, ctx: commands.Context):
        await ctx.reply("!elo {name}* - !rank {number} - !lobby {name}* - !sellout {name}* - !info {wave number} - *Optional, if not provided streamer name is used.")

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
        try:
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
                    end_string = " 🤡"
                case _:
                    end_string = ""
            try:
                await ctx.reply(f"{playername} {start_string} {stats["overallElo"]} Elo ({stats["overallPeakEloThisSeason"]} Peak){end_string}")
            except Exception:
                await ctx.reply(f"No data available for {playername}")
        except Exception:
            traceback.print_exc()
            await ctx.reply(f"Bot error 😭")
    
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
        
        await ctx.reply(f"{stats["profile"][0]["playerName"]} is Rank {rank}, {stats["overallElo"]} Elo ({stats["overallPeakEloThisSeason"]} Peak)")
    
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
                print(response.status, response.text)
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
        
        # Calculate average elo for each team
        west_players = game[2]
        east_players = game[3]
        team1_avg_elo = sum(float(p[1]) for p in west_players) / len(west_players)
        team2_avg_elo = sum(float(p[1]) for p in east_players) / len(east_players)
        
        # Calculate elo changes
        team1_elo_change = calculate_elo_change(team1_avg_elo, team2_avg_elo)
        team2_elo_change = calculate_elo_change(team2_avg_elo, team1_avg_elo)
        
        players_str = ", ".join([f"{player[0]}: {player[1]}" for player in west_players]) + " vs. " + ", ".join([f"{player[0]}: {player[1]}" for player in east_players])
        await ctx.reply(f"{players_str} (±{team1_elo_change} / ±{team2_elo_change})")
    
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
                await ctx.reply(f"Bot error 😭")
                return
            try:
                game = json.loads(await response.text())
            except Exception:
                await ctx.reply(f"Bot error 😭")
                return
        
        if not game:
            await ctx.reply(f"{name} is not in game currently.")
            return
        name = name.lower()
        team_one, team_two = game[2], game[3]
        players = {p[0].lower(): (int(p[1]), p[0]) for p in team_one + team_two}
        if name not in players:
            await ctx.reply(f"Could not find your name in the game.")
            return
        
        if name == team_one[0][0].lower():  # P1
            you, teammate = players[name], players[team_one[1][0].lower()]
            opponent, other = players[team_two[0][0].lower()], players[team_two[1][0].lower()]
        elif name == team_one[1][0].lower():  # P2
            you, teammate = players[name], players[team_one[0][0].lower()]
            opponent, other = players[team_two[1][0].lower()], players[team_two[0][0].lower()]
        elif name == team_two[0][0].lower():  # P3
            you, teammate = players[name], players[team_two[1][0].lower()]
            opponent, other = players[team_one[1][0].lower()], players[team_one[0][0].lower()]
        elif name == team_two[1][0].lower():  # P4
            you, teammate = players[name], players[team_two[0][0].lower()]
            opponent, other = players[team_one[0][0].lower()], players[team_one[1][0].lower()]
        else:
            await ctx.reply(f"Could not find your name in the game.")
            return
        
        sellout_score = you[0] + other[0] - teammate[0] - opponent[0]
        recommendation = f"You should sell out {teammate[1].replace(".", "")}. JULES" if sellout_score > 0 else f"You shouldn't sell out {teammate[1].replace(".", "")}. JULES"
        
        await ctx.reply(f"{you[1].replace(".", "")} Sellout Score: {sellout_score}. {recommendation}")
    
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
        await ctx.reply(f"Wave {wave} base recommended value is {recc_values[wave-1]}")

if __name__ == "__main__":
    bot = Bot()
    bot.run()