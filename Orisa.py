from os import write
import discord, datetime, asyncio, time, re
from dateutil import parser
from pytz import timezone
from discord import NotFound, Intents
from modules.tables import DBService
from modules.core import CoreService
from modules.practice import practice
from modules.utils import writeToFile
from modules.reaper import Reaper
from modules.hermes import Hermes
from discord.utils import get
from discord.ext import tasks

class Orisa: 
    #Variables
    __TOKEN = None 
    __client = None
    __filename = None
    __START = None
    __numInstr = None
    __numBugs = None
    __dbservice = None
    __coreservice = None
    __channels = None
    __roles = None

    def __init__(self, token, channels, roles, bot_tasks):
        self.__TOKEN = token
        intents = Intents.default()
        intents.members = True
        activity = discord.Activity(type=discord.ActivityType.watching, name="over Numbani")
        self.__client = discord.Client(intents=intents, activity=activity)
        self.on_ready = self.__client.event(self.on_ready)
        self.on_message = self.__client.event(self.on_message)
        self.on_member_join = self.__client.event(self.on_member_join)
        self.__START = datetime.datetime.now()
        self.__filename = self.__START.strftime("%Y_%m_%d_%H_%M_%S") + ".log"
        self.__numBugs = 0
        self.__numInstr = 0
        self.__dbservice = DBService()
        self.__coreservice = CoreService()
        self.__channels = channels
        self.__roles = roles
        self.__bot_tasks = bot_tasks
        self.__reaper = Reaper(config=self.__bot_tasks.get("reaper", None), filename=self.__filename)
        self.__hermes = Hermes(settings=self.__bot_tasks.get("hermes", None), logfilename=self.__filename)

        if not self.__reaper.is_enabled:
            writeToFile(self.__filename, "Reaper config not found, disabled")
            self.__reaper = None

    async def graceful_death(self, loop):
        await self.log("Received termination signal")
        if self.__hermes.enabled:
            await self.log("Writing backup")
            self.__hermes.write_config()
        await self.log("Exiting")
        print("I am dead\n")
        loop.stop()

    def start(self):
        self.taco_message_nine_am.start()
        if self.__reaper:
            self.reaper_task.start()
        self.__client.run(self.__TOKEN, destructor=self.graceful_death)

    @tasks.loop(hours=6)
    async def hermes_backup_task(self):
        if self.__hermes.enabled:
            self.__hermes.write_config()
    
    @hermes_backup_task.before_loop
    async def hermes_setup(self):
        await self.__client.wait_until_ready()
        interval = self.__hermes.interval
        await self.log(f"[Hermes] [SLEEP] {interval} sec")
        await asyncio.sleep(interval)

    @tasks.loop(hours=24)
    async def taco_message_nine_am(self):
        config = self.__bot_tasks['taco_message']
        if not config['enabled']:
            return
        message_channel = self.__client.get_channel(config['channel'])
        message = config['message']
        if message_channel != None:
            await message_channel.send(message)
        else:
            await self.log("[Otto] [ERR] Could not locate task channel for task {}".format(self.__bot_tasks['taco_message']))

    @taco_message_nine_am.before_loop
    async def before(self):
        await self.__client.wait_until_ready()
        config = self.__bot_tasks['taco_message']
        if not config:
            await self.log("[Otto] [ERR] Cannot find config")
        if not config['enabled']:
            return
        now = datetime.datetime.now()
        if now.time() > config['time']:
            tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), config['time'])
            seconds = (tomorrow - now).total_seconds()
            await self.log("[Otto] [SLEEP] {:.2f} seconds".format(seconds))
            await asyncio.sleep(seconds)
        target_time = datetime.datetime.combine(now.date(), config['time'])
        seconds_until_target = (target_time - now.time()).total_seconds()
        await self.log('[Otto] [SLEEP] {:.2f} seconds'.format(seconds_until_target))
        await asyncio.sleep(seconds_until_target)

    @tasks.loop(hours=1)
    async def reaper_task(self): 
        all_online = self.__coreservice.get_online_users()
        for i in all_online.keys():
            to_reap = self.__reaper.reap(i, all_online[i])
            if to_reap == 1:
                await self.log(await self.__coreservice.off(user=i, role=get(self.__client.guilds[0].roles, id=self.__roles.get("online", None))))
                await self.log(f'[Reaper] Timeout ({self.__reaper.timeout} seconds) encountered for {i.name}, reaped successfully')
            elif to_reap == 2:
                await self.log(f'[Reaper] [ALERT] CheckOnlineTIme {i.name} has been online for {(datetime.datetime.now() - all_online[i]).total_seconds()} seconds')

    @reaper_task.before_loop
    async def reaper_task_setup(self):
        await self.__client.wait_until_ready()
        await asyncio.sleep(self.__reaper.setup())


    async def log(self, outputstr):
        logchannel = self.__client.get_channel(self.__channels['log'])
        if logchannel is not None:
            await logchannel.send(outputstr)
        else:
            writeToFile(self.__filename, "Error: Could not find log channel")
            print("Could not find log channel")
        writeToFile(self.__filename, outputstr)

    async def parse_time(self, time_matches, id):
        parsed_time = parser.parse(time_matches[0])
        timezones = self.__dbservice.get_all_timezones()
        sender_timezone = self.__dbservice.get_sender_timezone(id)
        timezones.remove(sender_timezone)            
        
        outputstr = "Parsed time {} {}\n".format(parsed_time.strftime("%I:%M %P"), sender_timezone)

        for i in timezones:
            converted_time = parsed_time.astimezone(timezone(i)).strftime("%I:%M %P")
            outputstr += "{} {}\n".format(converted_time, i)
        await self.log("Parsed time {} into {}".format(parsed_time, timezones))
        return outputstr
    
    async def on_ready(self):
        print("Live")
        await self.log("Logged in as {}".format(self.__client.user))
        
        config = {}
        if self.__hermes.read_config():
            config = self.__hermes.config
        self.__coreservice = await CoreService.construct(self.__filename, config=config, guild=self.__client.guilds[0])
        self.__dbservice = await DBService.construct(self.__filename)
        if self.__hermes.enabled:
            self.__hermes.attach_core(self.__coreservice)
            self.hermes_backup_task.start()
        
    async def on_member_join(self, member):
        welcomechannel = self.__client.get_channel(self.__channels['welcome'])
        
        if welcomechannel is not None:
            message = await welcomechannel.send(f'Welcome, {member.mention}. React to this message with a ✅ to accept the rules')
            
            await message.add_reaction('✅')

            def check(reaction, user):
                    return str(reaction.emoji) == '✅' and user == member        
            try:
                # 30 Day timeout
                user = (await self.__client.wait_for('reaction_add',  timeout=2592000, check=check))[1]
                await message.remove_reaction('✅', user)
                await message.delete()
            except asyncio.TimeoutError:
                await self.log(f"Welcome message {message.id} to {member.name} is not being tracked anymore, please ask them to rejoin or manually add Friend role")
                await message.delete()
                return
            except NotFound:
                writeToFile(self.__filename, "Error, message not found")
                pass
            
            role = get(self.__client.guilds[0].roles, id=self.__roles['friend'])    
        
            await user.add_roles(role) 
            
            outputstr = "Gave the {} role to {}".format(role.name, user.name)
            await self.log(outputstr)
            writeToFile(self.__filename, outputstr) 
    
    # @Orisa.__client.event
    async def on_message(self, message):

        if message.author == self.__client.user:
                return
        
        # Parse Time
        regex = r'\d{1,2}\s?(?:(?:am|pm)|(?::\d{1,2})\s?(?:am|pm)?)'
        time_matches = re.findall(regex, message.content.lower())
        if len(time_matches) > 0:
            outputstr = await self.parse_time(time_matches, message.author.id)
            await message.channel.send(outputstr)

        # Reaper Command
        if "!ack" in message.content.lower():
            users = [message.author]
            if len(message.mentions) > 0:
                users = message.mentions
            for i in users:
                if self.__reaper.ack(i):
                    await self.log(f"[Reaper] ACK {i.name}")
                elif await self.__coreservice.__is_online__(i):
                    await self.log(f"[Reaper] {i.name} not paged yet")
                else:
                    await self.log(f"[Reaper] {i.name} resolved")

        # Help/Information
        if "!status" in message.content.lower():
            duration = datetime.datetime.now() - self.__START
            outputstr = "The bot is online and has been running for {}\n".format(str(duration).split('.')[0])
            if "-v" in message.content.lower():
                outputstr += "In this session, \n"
                outputstr += "{} unique instructions have been processed\n".format(self.__numInstr + 1) # +1 for current instruction
                outputstr += "{} unique bugs have been reported\n".format(self.__numBugs)
                # Saving this space for any other meta information people might need
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)
        
        if "!needhealing" in message.content.lower() or "!ineedhealing" in message.content.lower(): 
            outputstr = "Hi, I'm Orisa, a bot made by Zoid to automate the boring stuff on this server. For a full list of commands and documentation follow the link below \n"
            outputstr += "https://bhavdeepsinghb.github.io/OrisaBot"
            await message.channel.send(outputstr)

        # Admin commands
        if "!destroygroup" in message.content.lower() and "team member" in [y.name.lower() for y in message.author.roles]:
            await self.__coreservice.destroygroup(message)
        
        if "!alloff" in message.content.lower() and "team member" in  [y.name.lower() for y in message.author.roles]:
            await self.__coreservice.alloff(message)

        if "!practice" in message.content.lower() and "team member" in [y.name.lower() for y in message.author.roles]:
            globalMap = self.__coreservice.get_online_users()
            await practice(message, globalMap, self.__client)


        # General User Commands

        # Core Service
        # Roles
        
        onlineRole = self.__roles.get("online", None)
        
        # Methods

        if "!on" in message.content.lower():
            await self.__coreservice.on(message, role=get(self.__client.guilds[0].roles, id=onlineRole))

        if "!smurf" in message.content.lower():
            await self.__coreservice.smurf(message)

        if message.content.lower() in ["!whoison", "!whoson", "!whoon", "!whothefuckison", "!whotfison"]:
            await self.__coreservice.whoison(message)

        if "!off" in message.content.lower():
            await self.__coreservice.off(message, role=get(self.__client.guilds[0].roles, id=onlineRole))

        if "!lmk" in message.content.lower():
            await self.__coreservice.lmk(message)

        if "!group" in message.content.lower():
            await self.__coreservice.group(message)

        if "!ungroup" in message.content.lower():
            await self.__coreservice.ungroup_helper(message)

        if "!whoisgrouped" in message.content.lower():
            await self.__coreservice.whoisgrouped(message)

        # Serviceless
        if "!bug" in message.content.lower():
            myID = '<@!317936860393635843>'
            await message.channel.send("Bug Reported, thank you.\n Ping {} for updates".format(myID))
            outputstr = "---------------------------------------BUG REPORTED--------------------------------------------"
            writeToFile(self.__filename, outputstr)
            self.__numBugs += 1
        
        # DB Service
        if "!sr" in message.content.lower():
            if "team member" in [y.name.lower() for y in message.author.roles]:
                await self.__dbservice.sr(message)
            else:
                outputstr = "Sorry, {}. You'll have to be a team member to do that".format(message.author.name)
                await message.channel.send(outputstr)
        
        if "!set" in message.content.lower():
            if "team member" in [y.name.lower() for y in message.author.roles]:
                await self.__dbservice.set(message)
            else:
                outputstr = "Sorry, {}. You'll have to be a team member to do that"

        if "!register" in message.content.lower():
            if "team member" in [y.name.lower() for y in message.author.roles]:
                await self.__dbservice.register(message)
            else:
                outputstr = "Sorry, {}. You'll have to be a team member to do that"


        #Misc - won't be written to log files
        if message.content.lower() == "f":
            await message.channel.send("{} has put some respecc on it".format(message.author.name))
        
        if message.content.lower() == "a":
            await message.channel.send("{} has assembled the Avengers!".format(message.author.name))
        
        if message.content.lower() == "x":
            await message.channel.send("{} has assembled the X-Men!".format(message.author.name))

        self.__numInstr += 1
