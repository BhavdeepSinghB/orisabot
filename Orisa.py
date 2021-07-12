from os import write
import discord, datetime, asyncio, time, re
from dateutil import parser
from pytz import timezone
from discord import NotFound, Intents
from modules.tables import DBService
from modules.core import CoreService
from modules.practice import practice
from modules.reaper import Reaper
from modules.hermes import Hermes
from modules.logging_service import LoggingService
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
        # Bot Token
        self.__TOKEN = token
        # Start time and filename for logs
        self.__START = datetime.datetime.now()
        filename = self.__START.strftime("%Y_%m_%d_%H_%M_%S")
        self.log = LoggingService(filename)
        self.log.sender = "ORISA"
        # Intents and activity setup
        intents = Intents.default()
        intents.members = True
        activity = discord.Activity(type=discord.ActivityType.watching, name="over Numbani")
        # Discord client setup
        self.__client = discord.Client(intents=intents, activity=activity)
        # Client events setup
        self.on_ready = self.__client.event(self.on_ready)
        self.on_message = self.__client.event(self.on_message)
        self.on_member_join = self.__client.event(self.on_member_join)
        # Metrics
        self.__numBugs = 0
        self.__numInstr = 0
        # Services setup
        self.__dbservice = DBService()
        self.__coreservice = CoreService()
        # Config file stuff 
        # TODO might want to change this around
        self.__channels = channels
        self.__roles = roles
        self.__bot_tasks = bot_tasks
        # Support services setup
        self.__reaper = Reaper(config=self.__bot_tasks.get("reaper", None), log=self.log)
        self.__hermes = Hermes(settings=self.__bot_tasks.get("hermes", None), log=self.log)
        

        if not self.__reaper.is_enabled:
            self.log.warn("Reaper disabled")
            self.__reaper = None

    async def graceful_death(self, loop):
        self.log.info("Received termination signal")
        if self.__hermes.enabled and self.__hermes.backup_on_death:
            self.log.info("Writing backup...")
            self.__hermes.write_config()
            self.log.info("Backup complete")
        else:
            self.log.warn("Skipping backup on death")
        try:
            await self.log.priv("Exiting...")
        except AttributeError as e:
            self.log.error(e)
        print("I am dead\n")
        loop.stop()

    def start(self):
        self.log.info("Starting taco message task")
        self.taco_message_nine_am.start()
        if self.__reaper:
            self.log.info("Starting reaper task")
            self.reaper_task.start()
        self.__client.run(self.__TOKEN, destructor=self.graceful_death)

    @tasks.loop(hours=6)
    async def hermes_backup_task(self):
        if self.__hermes.enabled:
            self.log.info("(hermes_task) Writing backup")
            self.__hermes.write_config()
    
    @hermes_backup_task.before_loop
    async def hermes_setup(self):
        await self.__client.wait_until_ready()
        if self.__hermes.enabled:
            interval = self.__hermes.interval
            self.log.info(f"(hermes_task) [SLEEP] {interval} sec")
            await asyncio.sleep(interval)

    @tasks.loop(hours=24)
    async def taco_message_nine_am(self):
        config = self.__bot_tasks['taco_message']
        if not config['enabled']:
            self.log.info("Taco Message task disabled")
            return
        message_channel = self.__client.get_channel(config.get('channel', None))
        message = config.get('message', '')
        if message_channel != None:
            await message_channel.send(message)
        else:
            self.log.error("(taco_task) Could not locate task channel for task {}".format(self.__bot_tasks['taco_message']))

    @taco_message_nine_am.before_loop
    async def before(self):
        await self.__client.wait_until_ready()
        config = self.__bot_tasks['taco_message']
        if not config:
            self.log.error("(taco_task) Cannot find config")
        if not config['enabled']:
            return
        now = datetime.datetime.now()
        if now.time() > config['time']:
            tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), config['time'])
            seconds = (tomorrow - now).total_seconds()
            self.log.info("(taco_task) [SLEEP] {:.2f} seconds".format(seconds))
            await asyncio.sleep(seconds)
        target_time = datetime.datetime.combine(now.date(), config['time'])
        seconds_until_target = (target_time - now.time()).total_seconds()
        self.log.info('(taco_task) [SLEEP] {:.2f} seconds'.format(seconds_until_target))
        await asyncio.sleep(seconds_until_target)

    @tasks.loop(hours=1)
    async def reaper_task(self): 
        all_online = self.__coreservice.get_online_users()
        for i in all_online.keys():
            to_reap = self.__reaper.reap(i, all_online[i])
            if to_reap == 1:
                self.log.info(await self.__coreservice.off(user=i, role=get(self.__client.guilds[0].roles, id=self.__roles.get("online", None))))
                self.log.info(f'[Reaper] Timeout ({self.__reaper.timeout} seconds) encountered for {i.name}, reaped successfully')
            elif to_reap == 2:
                try:
                    self.log.priv(f'[Reaper] [ALERT] CheckOnlineTIme {i.name} has been online for {(datetime.datetime.now() - all_online[i]).total_seconds()} seconds', type="WARN")
                except AttributeError as e:
                    self.log.error(e)

    @reaper_task.before_loop
    async def reaper_task_setup(self):
        await self.__client.wait_until_ready()
        # Reaper setup logs sleep time
        await asyncio.sleep(self.__reaper.setup())

    async def parse_time(self, time_matches, id):
        parsed_time = parser.parse(time_matches[0])
        timezones = self.__dbservice.get_all_timezones()
        self.log.info(f"(parse_time) Got timezones {timezones}")
        sender_timezone = self.__dbservice.get_sender_timezone(id)
        timezones.remove(sender_timezone)            
        outputstr = "Parsed time {} {}\n".format(parsed_time.strftime("%I:%M %P"), sender_timezone)
        for i in timezones:
            converted_time = parsed_time.astimezone(timezone(i)).strftime("%I:%M %P")
            outputstr += "{} {}\n".format(converted_time, i)
        self.log.info("Parsed time {} into {}".format(parsed_time, timezones))
        return outputstr
    
    async def on_ready(self):
        print("Live")
        logchannel = self.__client.get_channel(self.__channels['log'])
        self.log.log_channel = logchannel
        try:
            self.log.priv("Logged in as {}".format(self.__client.user))
        except AttributeError as e:
            self.log.error(e)
        service_config = {}
        if self.__hermes.enabled and self.__hermes.read_config():
            service_config = self.__hermes.config
        else:
            self.log.warn("Hermes disabled")
        self.__coreservice = await CoreService.construct(self.__filename, config=service_config, guild=self.__client.guilds[0], log=self.log)
        self.__dbservice = await DBService.construct(self.__filename, log=self.log)
        if self.__hermes.enabled:
            self.__hermes.attach_core(self.__coreservice)
            self.hermes_backup_task.start()
        
    async def on_member_join(self, member):
        try:
            self.log.priv(f"Member {member} has joined the server")
        except AttributeError as e:
            self.log.error(f"{e}")
        welcomechannel = self.__client.get_channel(self.__channels['welcome'])
        if welcomechannel:
            message = await welcomechannel.send(f'Welcome, {member.mention}. React to this message with a ✅ to accept the rules')
            await message.add_reaction('✅')
            def check(reaction, user):
                    return str(reaction.emoji) == '✅' and user == member        
            try:
                # 30 Day timeout
                user = (await self.__client.wait_for('reaction_add',  timeout=2592000, check=check))[1]
                self.log.info(f"Successfully received reaction from user {member}")
                await message.remove_reaction('✅', user)
                await message.delete()
            except asyncio.TimeoutError:
                try:
                    self.log.priv(f"Welcome message {message.id} to {member.name} is not being tracked anymore, please ask them to rejoin or manually add Friend role", type="WARN")
                except AttributeError as e:
                    self.log.error(e)
                await message.delete()
                return
            except NotFound:
                self.log.error("Error, message not found")
                pass
            
            role = self.__client.guilds[0].get_role(self.__roles['friend'])
            if role:
                await user.add_roles(role) 
                outputstr = "Gave the {} role to {}".format(role.name, user.name)
                try:
                    self.log.priv(outputstr)
                except AttributeError as e:
                    self.log.error(e)
                self.log.info(outputstr) 
            else:
                self.log.error(f"Could not find 'friend' role")
        else:
            self.log.error("Could not locate welcome channel")
    
    # @Orisa.__client.event
    async def on_message(self, message):

        if message.author == self.__client.user:
                return
        
        
        # Parse Time
        regex = r'\d{1,2}\s?(?:(?:am|pm)|(?::\d{1,2})\s?(?:am|pm)?)'
        time_matches = re.findall(regex, message.content.lower())
        if len(time_matches) > 0:
            self.log.info("Found time match, parsing...")
            outputstr = await self.parse_time(time_matches, message.author.id)
            await message.channel.send(outputstr)

        # Reaper Command
        if "!ack" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            if not self.__reaper.is_enabled:
                try:
                    await self.log.priv("No reaper instance found", type="ERR")
                except AttributeError as e:
                    self.log.error(e)
                return
            users = [message.author]
            if len(message.mentions) > 0:
                users = message.mentions
            for i in users:
                try:
                    if self.__reaper.ack(i):
                        await self.log.priv(f"[Reaper] ACK {i.name}", type="OK")
                    elif self.__coreservice.__is_online__(i):
                        await self.log.priv(f"[Reaper] {i.name} not paged yet", type="ERR")
                    else:
                        await self.log.priv(f"[Reaper] {i.name} resolved", type="OK")
                except AttributeError as e:
                    self.log.error(e)

        # Help/Information
        if "!status" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            duration = datetime.datetime.now() - self.__START
            outputstr = "The bot is online and has been running for {}\n".format(str(duration).split('.')[0])
            await message.channel.send(outputstr)
            self.log.info(outputstr)
        
        if "!needhealing" in message.content.lower() or "!ineedhealing" in message.content.lower(): 
            self.log.info(f"Received message: {message.content} from {message.author}")
            outputstr = "Hi, I'm Orisa, a bot made by Zoid to automate the boring stuff on this server. For a full list of commands and documentation follow the link below \n"
            outputstr += "https://bhavdeepsinghb.github.io/OrisaBot"
            await message.channel.send(outputstr)

        # Admin commands
        if self.__roles['privileged'] in [y.id for y in message.author.roles]:
            if "!destroygroup" in message.content.lower():
                self.log.info(f"Received message: {message.content} from {message.author}")
                await self.__coreservice.destroygroup(message)
    
            if "!alloff" in message.content.lower():
                self.log.info(f"Received message: {message.content} from {message.author}")
                await self.__coreservice.alloff(message)
    
            if "!practice" in message.content.lower():
                self.log.info(f"Received message: {message.content} from {message.author}")
                globalMap = self.__coreservice.get_online_users()
                await practice(message, globalMap, self.__client)

        # Core Service
        # Roles
        
        onlineRole = self.__roles.get("online", None)
        
        # Methods

        if "!on" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.on(message, role=get(self.__client.guilds[0].roles, id=onlineRole))

        if "!smurf" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.smurf(message)

        if message.content.lower() in ["!whoison", "!whoson", "!whoon", "!whothefuckison", "!whotfison"]:
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.whoison(message)

        if "!off" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.off(message, role=get(self.__client.guilds[0].roles, id=onlineRole))

        if "!lmk" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.lmk(message)

        if "!group" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.group(message)

        if "!ungroup" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.ungroup_helper(message)

        if "!whoisgrouped" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            await self.__coreservice.whoisgrouped(message)

        # Serviceless
        if "!bug" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            myID = '<@!317936860393635843>'
            await message.channel.send("Bug Reported, thank you.\n Ping {} for updates".format(myID))
            outputstr = "---------------------------------------BUG REPORTED--------------------------------------------"
            self.log.info(outputstr)
            self.__numBugs += 1
        
        # DB Service
        if "!sr" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            if self.__roles['privileged'] in [y.id for y in message.author.roles]:
                await self.__dbservice.sr(message)
            else:
                outputstr = "Sorry, {}. You'll have to be a team member to do that".format(message.author.name)
                self.log.warn(outputstr)
                await message.channel.send(outputstr)
        
        if "!set" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            if self.__roles['privileged'] in [y.id for y in message.author.roles]:
                await self.__dbservice.set(message)
            else:
                outputstr = "Sorry, {}. You'll have to be a team member to do that"
                self.log.warn(outputstr)
                await message.channel.send(outputstr)

        if "!register" in message.content.lower():
            self.log.info(f"Received message: {message.content} from {message.author}")
            if self.__roles['privileged']in [y.id for y in message.author.roles]:
                await self.__dbservice.register(message)
            else:
                outputstr = "Sorry, {}. You'll have to be a team member to do that"
                self.log.warn(outputstr)
                await message.channel.send(outputstr)

        #Misc - won't be written to log files
        if message.content.lower() == "f":
            await message.channel.send("{} has put some respecc on it".format(message.author.name))
        
        if message.content.lower() == "a":
            await message.channel.send("{} has assembled the Avengers!".format(message.author.name))
        
        if message.content.lower() == "x":
            await message.channel.send("{} has assembled the X-Men!".format(message.author.name))

