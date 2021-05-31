from os import write
import discord, datetime, asyncio, time
from discord import NotFound, Intents
from modules.tables import DBService
from modules.core import CoreService
from modules.practice import practice
from modules.utils import writeToFile
from discord.utils import get
from discord.ext import tasks
from config_alfred import ALFRED_TOKEN, channels, roles, bot_tasks
# from config_orisa import ORISA_TOKEN, ALFRED_TOKEN, channels, roles, bot_tasks


TOKEN = ALFRED_TOKEN

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

    def __init__(self, token):
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

    def start(self):
        self.taco_message_nine_am.start()
        self.__client.run(self.__TOKEN)

    @tasks.loop(hours=24)
    async def taco_message_nine_am(self):
        message_channel = self.__client.get_channel(bot_tasks['taco_message']['channel'])
        if message_channel != None:
            await self.log(f'[Tasks] Sending automated message for task taco_message')
            await message_channel.send(bot_tasks['taco_message']['message'])
        else:
            self.log("[Tasks] Error: Could not locate task channel for task {}".format(bot_tasks['taco_message']))

    @taco_message_nine_am.before_loop
    async def before(self):
        await self.__client.wait_until_ready()
        now = datetime.datetime.now()
        if now.time() > bot_tasks['taco_message']['time']:
            tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(0))
            seconds = (tomorrow - now).total_seconds()
            await self.log("[Tasks] Sleeping for {:.2f} seconds till {}".format(seconds, bot_tasks["taco_message"]["time"]))
            await asyncio.sleep(seconds)
        target_time = datetime.datetime.combine(now.date(), bot_tasks['taco_message']['time'])
        seconds_until_target = (target_time - now).total_seconds()
        await self.log('[Tasks] Sleeping for {:.2f} seconds till {}'.format(seconds_until_target, target_time))
        await asyncio.sleep(seconds_until_target)
        
    async def log(self, outputstr):
        logchannel = self.__client.get_channel(self.__channels['log'])
        if logchannel is not None:
            await logchannel.send(outputstr)
        writeToFile(self.__filename, outputstr)
    
    async def on_ready(self):
        print("Live")
        self.log("Logged in as {}".format(self.__client.user))
        self.__coreservice = await CoreService.construct(self.__filename)
        self.__dbservice = await DBService.construct(self.__filename)
        
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
        
        # Help/Information
        if "!status" in message.content.lower():
            if message.author.name == "Orisa":
                return
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
            globalMap = await self.__coreservice.get_online_users()
            await practice(message, globalMap, self.__client)

        # General User Commands
        # Core Service
        if "!on" in message.content.lower():
            await self.__coreservice.on(message)

        if "!smurf" in message.content.lower():
            await self.__coreservice.smurf(message)

        if message.content.lower() in ["!whoison", "!whoson", "!whoon", "!whothefuckison", "!whotfison"]:
            await self.__coreservice.whoison(message)

        if "!off" in message.content.lower():
            await self.__coreservice.off(message)

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

o = Orisa(TOKEN)
o.start()
