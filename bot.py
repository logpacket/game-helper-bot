import os, json, re
import discord, asyncio

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib import parse
from riot_api import *

app = discord.Client()
mstatus = 0
botid = ""

token = os.getenv("TOKEN")
lol_apikey = os.getenv("API_KEY")
if not token:
    json_data = open(os.getcwd() + "/token/.config.json", encoding='utf-8').read()
    config_json = json.loads(json_data)
    token = config_json["token"]

@app.event
async def on_ready():
    global botid
    print('Logged in as')
    print(app.user.name)
    print(app.user.id)
    print('------')
    game = discord.Game("Game Helper | !helpme")
    botid = await app.application_info()
    await app.change_presence(status=discord.Status.online, activity=game)


@app.event
async def on_message(message):
    global mstatus, botid
    if message.author.bot and message.author.id == botid.id:
        if mstatus == 1:
            await message.add_reaction("\u2b55") # O
            await message.add_reaction("\u274c") # X
            mstatus = mstatus - 1
        else:
            return None

    if message.content == "!helpme":
        desc_text = "{0} \n{1} \n{2} \n{3} \n{4}".format("!helpme : 명령어 목록 불러오기", \
                                                    "!owsearch : 오버워치 전적 검색하기", \
                                                    "!lolsearch : 롤 소환사 검색하기", \
                                                    "!muteall : 현재 보이스 채널에 있는 유저들 모두 음소거 시키기", \
                                                    "!unmuteall : 모든 사용자 음소거 해제하기")
        
        embed = discord.Embed(title="명령어 목록", description=desc_text, color=0x6FA8DC)
        await message.channel.send(embed=embed)

    if message.content == "!owsearch":
        embed = discord.Embed(title="Overwatch 점수 검색", description="'배틀태그#숫자' 형식으로 입력해주세요.", color=0x82CC62)
        embed.set_image(url="https://bnetcmsus-a.akamaihd.net/cms/blog_header/q4/Q4K237E1EGPI1467079634956.jpg")

        await message.channel.send(embed=embed)

        def check(m):
            return m.author == message.author and m.channel == message.channel

        try:    
            m = await app.wait_for('message',timeout=25.0, check=check)
        except asyncio.TimeoutError:
            await message.channel.send("시간초과!")
        else:
            battletag_bool = bool(re.search('.[#][0-9]', m.content))
            if battletag_bool:
                battletag = m.content.replace("#", "-")
                async with message.channel.typing():
                    req = Request("https://playoverwatch.com/ko-kr/career/pc/" + parse.quote(battletag))
                    res = urlopen(req)

                    bs = BeautifulSoup(res, "html.parser")
                    roles = bs.findAll("div", attrs={"class": "competitive-rank-tier"})
                    scores = bs.findAll("div", attrs={"class": "competitive-rank-level"})
                    public_status = bs.findAll("p", attrs={"class": "masthead-permission-level-text"})


                competitive_roles = [i.get("data-ow-tooltip-text") for i in roles[:len(roles)//2]]
                competitive_score = [i.text for i in scores[:len(scores)//2]]

                if not public_status:
                    await message.channel.send("프로필이 존재하지 않습니다. 배틀태그와 뒤에 숫자를 다시 확인해 주세요.")
                else:
                    if public_status[0].text == "비공개 프로필":
                        await message.channel.send("비공개 프로필입니다. 프로필 공개 설정을 공개로 바꾼 뒤에 사용해 주세요.")
                    else:
                        comp_data = bs.find("div", attrs={"id": "competitive","data-mode": "competitive"})
                        heroes = comp_data.findAll("div", attrs={"class": "ProgressBar-title"})
                        play_time = comp_data.findAll("div", attrs={"class": "ProgressBar-description"})
                        comp_heroes = []

                        for h in heroes:
                            comp_heroes.append([h])
                        
                        for i in range(len(play_time)):
                            comp_heroes[i].append(play_time[i])

                        score_result = ""
                        top_five_result = ""
                        top_five = [[d[0].text, d[1].text] for d in comp_heroes] if len(comp_heroes) <= 5 else [[d[0].text, d[1].text] for d in comp_heroes[:5]]

                        def format_time(s):
                            t = s.split(":")
                            if len(t) == 2:
                                # MM:SS
                                return "{0} 분".format(str(int(t[0])))
                            elif len(t) == 3:
                                # HH:MM:SS
                                return "{0} 시간".format(str(int(t[0])))
                            else:
                                return "0 분"

                        if len(competitive_roles) == 0 and len(competitive_score) == 0:
                            score_result = "아직 배치를 덜본것 같군요! 점수가 없습니다."
                        else:
                            for i in range(len(competitive_roles)):
                                score_result = score_result + competitive_roles[i] + " : " + competitive_score[i] + "\n"
                            score_result = score_result + "입니다."
                        
                        for i, h in enumerate(top_five):
                            top_five_result += "{0}. {1}: {2}\n".format(str(i+1), h[0], format_time(h[1]))


                        embed = discord.Embed(title=battletag.split("-")[0] + " 님의 현재 시즌 경쟁전 점수", description=score_result, color=0x82CC62)
                        embed2 = discord.Embed(title="경쟁전 상위 영웅", description=top_five_result, color=0x82CC62)

                        await message.channel.send(embed=embed)
                        await message.channel.send(embed=embed2)
            else:
                # Invalid
                await message.channel.send("배틀태그가 유효하지 않습니다.")

    if message.content == "!lolsearch":
        embed = discord.Embed(title="롤 소환사 검색", description="소환사 이름을 입력하세요 \n단, 소환사 이름만 입력하세요!", color=0x82CC62)
        await message.channel.send(embed=embed)

        def check(m):
            return m.author == message.author and m.channel == message.channel

        try:
            m = await app.wait_for('message',timeout=25.0, check=check)
        except asyncio.TimeoutError:
            await message.channel.send("시간초과!")
        else:
            async with message.channel.typing():
                summoner = Summoner(m.content)

            if summoner.account_id == "":
                # Misinput. Aborting
                await message.channel.send("소환사 이름을 잘못 입력하셨습니다.")
            else:
                info = summoner.summoner_info
                if info:
                    info = info[0]
                    msg = info.get("message")
                    if not msg:
                        name = info.get("summonerName", "NULL")
                        tier = info.get("tier", "")
                        rank = info.get("rank" "")
                        win_rate = "{} %".format(int(summoner.recent_winning_rate*100))
                        result_url = "http://www.op.gg/summoner/userName=" + parse.quote(name)

                        desc_text = "소환사 이름 : {0}\n \
                                    티어 : {1} {2}\n \
                                    최근 랭크 게임 승률 : {3}\n".format(name, tier, rank, win_rate)
                        embed = discord.Embed(title="소환사 검색 결과", description=desc_text, url=result_url, color=0x82CC62)
                    else:
                        desc_text = "없는 소환사 입니다."
                        embed = discord.Embed(title="소환사 검색 결과", description=desc_text, color=0x82CC62)
                    
                    await message.channel.send(embed=embed)
                else:
                    name = summoner.account.get("name")
                    if name:
                        # Exists, but no recent comp play
                        desc_text = "소환사 이름 : {0}\n \
                                    티어 : 플레이 내역이 없습니다.\n \
                                    최근 랭크 게임 승률 : 플레이 내역이 없습니다.\n".format(name)
                        embed = discord.Embed(title="소환사 검색 결과", description=desc_text, color=0x82CC62)
                        await message.channel.send(embed=embed)
                    else:
                        #???
                        await message.channel.send("???????")
                    
    if message.content == "!muteall":
        if message.author.voice is None:
            await message.channel.send("이 기능을 사용하려면 보이스 채널에 들어가 있어야 합니다!")
        else:
            mstatus = mstatus + 1
            embed = discord.Embed(title="Among Us 전용 전체 음소거 기능", description="현재 음성채널에 있는 모든 사용자를 음소거하겠습니까? \n원하시면 :o:, 아니면 :x:를 눌러주세요.", color=0xFFD966)

            await message.channel.send(embed=embed)

            def check(reaction, user):
                return user == message.author and (str(reaction.emoji) == "\u2b55" or str(reaction.emoji) == "\u274c")

            try:
                reaction, user = await app.wait_for('reaction_add', timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await message.channel.send("시간초과!")

            else:
                if str(reaction.emoji) == "\u2b55":
                    # await message.channel.send(administrator_id)
                    member_list = message.author.voice.channel.members
                    async with message.channel.typing():
                        for member in member_list:
                            await member.edit(mute=True, reason="Among Us Player Mute All")

                    await message.channel.send("음소거 완료!")

                elif str(reaction.emoji) == "\u274c":
                    await message.channel.send("싫음 소환하지를 마. 귀찮게.")

    if message.content == "!unmuteall":
        member_list = message.author.voice.channel.members
        async with message.channel.typing():
            for member in member_list:
                await member.edit(mute=False)
        
        await message.channel.send("음소거 해제 완료!")
        
    if "개" in message.content or message.content == "!doge":
        await message.channel.send("https://i.kym-cdn.com/entries/icons/original/000/013/564/doge.jpg")

app.run(token)