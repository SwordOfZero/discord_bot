import sqlite3
import discord
from discord.ext import commands
import random, logging, sys
import character as ch


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True
dashes = ['\u2680', '\u2681', '\u2682', '\u2683', '\u2684', '\u2685']

bot = commands.Bot(command_prefix='D&D ', intents=intents)

class RandomThings(commands.Cog, discord.Client):

    def __init__(self, bot):
        self.bot = bot

    async def check_access(self, access, member):
        ret = False
        for ac in access:
            for role in member.author.roles:
                if role.name == ac:
                    ret = True
        return ret

    async def correct_search(self, information, type='string'):
        if type == "string":
            information = str(information)
            information = information[2:-3]
        elif type == "integer":
            information = str(information)
            information = information[1:-2]
        return information

    @commands.command(name='dice')
    async def dice(self, ctx, max_int=20):
        if await self.check_access(['witness', "Администратор", 'master'], ctx):
            num = random.randint(1, int(max_int))
            await ctx.send(num)

    @commands.command(name='role')
    async def role(self, ctx):
        if await self.check_access(["Администратор"], ctx):
            role_name = str(ctx.message.content).split(' ')[-1]
            role = None
            name = ' '.join(str(ctx.message.content).split(' ')[2:-1])
            member = None
            for i in range(0, len(ctx.guild.members)):
                if ctx.guild.members[i].name == name:
                    member = ctx.guild.members[i]
                    member_number = i
            for i in range(0, len(ctx.guild.roles)):
                if ctx.guild.roles[i].name == role_name:
                    role = ctx.guild.roles[i].id
            if role != None and member != None:
                await ctx.guild.members[member_number].add_roles(ctx.guild.get_role(role))
                await ctx.send(f"{member.mention} была выдана роль {role_name}")
            if role == None:
                await ctx.send("Не существует такой роли")
            if member == None:
                await ctx.send("Не существует такого участника")
        else:
            await ctx.send("Для этой комманды нужна роль Администратор")

    @commands.command(name='terminate')
    async def terminate(self, ctx):
        if await self.check_access(["Администратор"], ctx):
            for guild in bot.guilds:
                for channel in guild.channels:
                    if channel.name == 'dnd-bot':
                        await channel.send("!сейчас будут проходить технические работы!\nбот временно выключен")
            sys.exit()
        else:
            await ctx.send('ОТКАЗАНО В ДОСТУПЕ\nДоступ к этой команде имеют только люди с ролью "Администратор"')

    @commands.command(name="help!")
    async def help(self, ctx):
        await ctx.send('\n'.join(['dice "количество граней кости"', 'role "имя" "роль"', 'terminate',
                                  'connect_game "номер игры"',
                                  'backpack set "содержимое"',
                                  'backpack add "содержимое"',
                                  'backpack delete "содержимое"',
                                  'game_list',
                                  'game_stop',
                                  'create_game "номер игры"',
                                  'show game/level/skills/description/backpack',
                                  'set_skills "шесть чисел через запятую от 8 до 15, сумма которых не больше 75"',
                                  'set_description "описание"', 'level_up "имя игрока"']))

    @commands.command(name='game_list')
    async def game_list(self, ctx):
        db_name = ctx.message.guild.name
        db_name = db_name.replace(' ', '_')
        db_name = db_name.replace('&', 'and')
        game = cur.execute('SELECT in_game FROM {}'.format(db_name)
                           ).fetchall()
        game = [str(await self.correct_search(x, 'integer')) for x in game]
        await ctx.send(', '.join(game))

    @commands.command(name='game_stop')
    async def game_stop(self, ctx):
        if await self.check_access(["master"], ctx):
            db_name = ctx.message.guild.name
            db_name = db_name.replace(' ', '_')
            db_name = db_name.replace('&', 'and')
            author = ctx.message.author.id
            game = cur.execute('SELECT in_game FROM {} WHERE user_id == ?'.format(db_name),
                               (author,)).fetchone()
            game = int(await self.correct_search(game, 'integer'))
            if game == 0:
                await ctx.send("Вы вне игры")
            else:
                game_lenght = len(cur.execute('SELECT * FROM {} WHERE in_game == ?'.format(db_name),
                               (game,)).fetchall())
                id = cur.execute('SELECT user_id FROM {} WHERE in_game == ?'.format(db_name),
                               (game,)).fetchall()
                id = [int(await self.correct_search(x, 'integer')) for x in id]
                for i in range(0, game_lenght):
                    cur.execute('UPDATE {} SET in_game == ? WHERE user_id == ?'.format(db_name),
                                (0, id[i]))
                    cur.execute('UPDATE {} SET lvl == ? WHERE user_id == ?'.format(db_name),
                                (0, id[i]))
                    cur.execute('UPDATE {} SET skills == ? WHERE user_id == ?'.format(db_name),
                                ('', id[i]))
                    cur.execute('UPDATE {} SET description == ? WHERE user_id == ?'.format(db_name),
                                ('', id[i]))
                    cur.execute('UPDATE {} SET backpack == ? WHERE user_id == ?'.format(db_name),
                                ('', id[i]))
                    base.commit()
                await ctx.send('Игра остановлена')
        else:
            await ctx.send('Необходима роль master')

    @commands.command(name='create_game')
    async def create_game(self, ctx):
        if await self.check_access(["master"], ctx):
            content = int(str(ctx.message.content).split(' ')[2])
            db_name = ctx.message.guild.name
            db_name = db_name.replace(' ', '_')
            db_name = db_name.replace('&', 'and')
            author = ctx.message.author.id
            game = cur.execute('SELECT in_game FROM {}'.format(db_name)
                               ).fetchall()
            game = [int(await self.correct_search(x, 'integer')) for x in game]
            m_game = cur.execute('SELECT in_game FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
            m_game = int(await self.correct_search(m_game, 'integer'))
            if content in game:
                await ctx.send('Игра с таким номером уже существует')
            else:
                if m_game != 0:
                    await ctx.send("Для создания игры вам нужно выйти из текущей игры")
                else:
                    cur.execute('UPDATE {} SET in_game == ? WHERE user_id == ?'.format(db_name),
                                (content, author))
                    base.commit()
                    await ctx.send(f'Вы в игре {content}')
        else:
            await ctx.send('Необходима роль master')

    @commands.command(name='connect_game')
    async def connect_game(self, ctx):
        content = int(str(ctx.message.content).split(' ')[2])
        db_name = ctx.message.guild.name
        db_name = db_name.replace(' ', '_')
        db_name = db_name.replace('&', 'and')
        author = ctx.message.author.id
        games = cur.execute('SELECT in_game FROM {}'.format(db_name)
                           ).fetchall()
        games = [int(await self.correct_search(x, 'integer')) for x in games]
        skills = cur.execute('SELECT skills FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
        skills = str(await self.correct_search(skills))
        description = cur.execute('SELECT description FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
        description = str(await self.correct_search(description))
        game = cur.execute('SELECT in_game FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
        game = int(await self.correct_search(game, 'integer'))
        if content == 0:
            cur.execute('UPDATE {} SET in_game == ? WHERE user_id == ?'.format(db_name),
                        (0, author))
            cur.execute('UPDATE {} SET lvl == ? WHERE user_id == ?'.format(db_name),
                        (0, author))
            cur.execute('UPDATE {} SET skills == ? WHERE user_id == ?'.format(db_name),
                        ('', author))
            cur.execute('UPDATE {} SET description == ? WHERE user_id == ?'.format(db_name),
                        ('', author))
            cur.execute('UPDATE {} SET backpack == ? WHERE user_id == ?'.format(db_name),
                        ('', author))
            base.commit()
            await ctx.send(f"Вы вышли из игры")
        elif len(skills) > 4 and len(description) > 10 and game == 0 and game in games:
            cur.execute('UPDATE {} SET in_game == ? WHERE user_id == ?'.format(db_name),
                                      (content, author))
            cur.execute('UPDATE {} SET lvl == ? WHERE user_id == ?'.format(db_name),
                        (1, author))
            base.commit()
            await ctx.send(f"Вы в игре {content}")
        else:
            if len(skills) < 4:
                await ctx.send(f"Вы не указали характеристики\nВход в игру не доступен")
            if len(description) < 10:
                await ctx.send(f"Вы не указали описание персонажа\nВход в игру не доступен")
            if game != 0:
                await ctx.send(f"Вы уже находитесь в игре\nВход в другую игру не доступен")
            if content not in games:
                await ctx.send(f"Данной игры не существует")

    @commands.command(name='show')
    async def show(self, ctx):
        content = str(ctx.message.content).split(' ')
        if len(content) > 2:
            names = ['сила', 'ловкость', 'телосложение', 'интелект', 'мудрость', 'харизма']
            db_name = ctx.message.guild.name
            db_name = db_name.replace(' ', '_')
            db_name = db_name.replace('&', 'and')
            author = ctx.message.author.id
            if content[2] == 'skills':
                inf = cur.execute('SELECT skills FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
                inf = await self.correct_search(inf)
                if len(inf) == 0:
                    await ctx.send("Вы ещё не установили характеристики")
                else:
                    inf = inf.split(';')
                    ret = []
                    for i in range(0, 6):
                        ret.append(f'{names[i]}: {inf[i]}')
                    ret = '\n'.join(ret)
                    await ctx.send(ret)
            elif content[2] == 'game':
                inf = cur.execute('SELECT in_game FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
                inf = int(await self.correct_search(inf, 'integer'))
                if inf == 0:
                    await ctx.send("Вы находитесь вне игры")
                else:
                    await ctx.send(f"Вы находитесь в игре {inf}")
            elif content[2] == 'backpack':
                inf = cur.execute('SELECT backpack FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
                inf = str(await self.correct_search(inf))
                if len(inf) == 0:
                    await ctx.send("Рюкзак пуст")
                else:
                    await ctx.send(inf)
            elif content[2] == 'level':
                inf = cur.execute('SELECT lvl FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
                inf = int(await self.correct_search(inf, 'integer'))
                if inf == 0:
                    await ctx.send("Вы находитесь вне игры")
                else:
                    await ctx.send(str(inf))
            elif content[2] == 'description':
                inf = cur.execute('SELECT description FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
                inf = str(await self.correct_search(inf))
                if len(inf) < 4:
                    await ctx.send("Вы ещё не добавили описание")
                else:
                    await ctx.send(inf)
            else:
                await ctx.send("ОШИБКА\nНе корректный аргумент")
        else:
            await ctx.send("ОШИБКА\nОтсутствуют аргументы")

    @commands.command(name='level_up')
    async def level_up(self, ctx):
        if await self.check_access(["master"], ctx):
            name = ' '.join(str(ctx.message.content).split(' ')[2::])
            db_name = ctx.message.guild.name
            db_name = db_name.replace(' ', '_')
            db_name = db_name.replace('&', 'and')
            author = ctx.message.author.id
            member_number = None
            print(name)
            for i in range(0, len(ctx.guild.members)):
                if ctx.guild.members[i].name == name:
                    member_number = i
            player_game = int(await self.correct_search(cur.execute('SELECT in_game FROM {} WHERE user_id == ?'
                                                                    .format(db_name),
                              (ctx.guild.members[member_number].id,)).fetchone(), 'integer'))
            master_game = int(await self.correct_search(cur.execute('SELECT in_game FROM {} WHERE user_id == ?'
                                                                    .format(db_name),
                              (author,)).fetchone(), 'integer'))
            print(master_game, player_game, member_number, name, ctx.guild.members[member_number].id)
            if master_game == player_game and master_game != 0:
                inf = cur.execute('SELECT lvl FROM {} WHERE user_id == ?'.format(db_name),
                                  (ctx.guild.members[member_number].id,)).fetchone()
                inf = int(await self.correct_search(inf, 'integer'))
                cur.execute('UPDATE {} SET lvl == ? WHERE user_id == ?'.format(db_name),
                            (inf + 1, ctx.guild.members[member_number].id))
                base.commit()
                await ctx.send('Уровень повышен')
            else:
                await ctx.send('Вы и игрок находитесь вне игры или в разных играх')
        else:
            await ctx.send('Для этой команды нужна роль master')

    @commands.command(name='set_description')
    async def set_description(self, ctx):
        db_name = ctx.message.guild.name
        db_name = db_name.replace(' ', '_')
        db_name = db_name.replace('&', 'and')
        author = ctx.message.author.id
        content = str(ctx.message.content)[20::]
        cur.execute('UPDATE {} SET description == ? WHERE user_id == ?'.format(db_name),
                    (content, author))
        base.commit()

    @commands.command(name='backpack')
    async def backpack(self, ctx):
        db_name = ctx.message.guild.name
        db_name = db_name.replace(' ', '_')
        db_name = db_name.replace('&', 'and')
        author = ctx.message.author.id
        if str(ctx.message.content).split(' ')[2] == 'set':
            content = str(ctx.message.content)[16::]
            cur.execute('UPDATE {} SET backpack == ? WHERE user_id == ?'.format(db_name),
                        (content, author))
            base.commit()
        elif str(ctx.message.content).split(' ')[2] == 'add':
            content = str(ctx.message.content)[16::]
            current = cur.execute('SELECT backpack FROM {} WHERE user_id == ?'.format(db_name),
                          (author,)).fetchone()
            current = str(await self.correct_search(current))
            ret = current + ', ' + content
            cur.execute('UPDATE {} SET backpack == ? WHERE user_id == ?'.format(db_name),
                        (ret, author))
            base.commit()
        elif str(ctx.message.content).split(' ')[2] == 'delete':
            content = str(ctx.message.content)[19::]
            current = cur.execute('SELECT backpack FROM {} WHERE user_id == ?'.format(db_name),
                                  (author,)).fetchone()
            current = str(await self.correct_search(current))
            if content in current:
                if len(current) == len(content) or current[-len(content)::]:
                    current = current.replace(content, '')
                else:
                    current = current.replace(content, ', ')
                cur.execute('UPDATE {} SET backpack == ? WHERE user_id == ?'.format(db_name),
                            (current, author))
                base.commit()

    @commands.command(name='set_skills')
    async def set_skills(self, ctx):
        names = ['сила', 'ловкость', 'телосложение', 'интелект', 'мудрость', 'харизма']
        db_name = ctx.message.guild.name
        db_name = db_name.replace(' ', '_')
        db_name = db_name.replace('&', 'and')
        author = ctx.message.author.id
        db_game = cur.execute('''SELECT in_game FROM {} WHERE user_id == ?'''.format(db_name),(ctx.message.author.id,)).fetchone()
        db_game = int(await self.correct_search(db_game, 'integer'))
        if db_game == 0:
            try:
                content = str(ctx.message.content).split(' ')[2]
                content = content.split(',')
                content = [int(x) for x in content]
                sk = ch.check_skill_point(content)
                ret = ''
                ret_dop = ''
                if sk != None:
                    for i in range(0, 6):
                        ret_dop += f'{names[i]}: {sk[i]};'
                        ret += f'{sk[i]};'
                    ret = ret[0:-1]
                    ret_dop = ret_dop[0:-1]
                    ret_dop = ret_dop.split(";")
                    ret_dop = '\n'.join(ret_dop)
                    await ctx.send(ret_dop)
                    cur.execute('UPDATE {} SET skills == ? WHERE user_id == ?'.format(db_name),
                                (ret, author))
                    base.commit()
                else:
                    await ctx.send("неправильная команда")
            except:
                await ctx.send("неправильная команда")
        else:
            await ctx.send("Нельзя изменять свои характеристики после начала игры")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Команда не найдена!\nДля получения списка команд введите "D&D help!"')

@bot.event
async def on_ready(): # событие подключения к серверу
    for guild in bot.guilds:
        for channel in guild.channels:
            if channel.name == 'dnd-bot':
                await channel.send('Dungeon master запущен')

    global base, cur
    base = sqlite3.connect('dnd.db')
    cur = base.cursor()

@bot.event
async def on_member_join(member):
    channel = bot.get_guild(member.guild.id).channels[2]
    for i in range(0, len(member.guild.roles)):
        if member.guild.roles[i].name == 'witness':
            role = member.guild.roles[i].id
    await member.add_roles(member.guild.get_role(role))
    await channel.send(
        f"Добро пожаловать {member.name}!\nВам была выдана роль 'witness'"
    )


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author != bot.user:
        pass
    else:
        return

    db_name = message.guild.name
    db_name = db_name.replace(' ', '_')
    db_name = db_name.replace('&', 'and')
    base.execute('CREATE TABLE IF NOT EXISTS {}(user_id INT, lvl INT, in_game INT, skills STRING, backpack STRING, description STRING)'.format(db_name))
    base.commit()
    log = cur.execute('SELECT * FROM {} WHERE user_id == ?'.format(db_name),(message.author.id,)).fetchone()
    if log == None:
        cur.execute('INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?)'.format(db_name),(message.author.id,0,0,'','',''))
        base.commit()

bot.add_cog(RandomThings(bot))

TOKEN = "OTYyMDAyNTMwNjQ3MzEwNDI2.YlBMrA.G_nqg3FX1FCT0fb2SmFuqSHDFeQ"
bot.run(TOKEN)