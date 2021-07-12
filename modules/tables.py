import sqlite3, asyncio, statistics, copy, datetime, os
from sqlite3.dbapi2 import connect
from pathlib import Path
from modules.logging_service import LoggingService

class DBService:
    # Variables
    __conn = None
    __cursor = None
    __filename = None
    __sr_table_name = ""
    
    @classmethod
    async def construct(cls, filename, log=None):
        self = DBService()
        if log:
            self.log = copy.copy(log)
        else:
            self.log = LoggingService(filename=datetime.datetime.strftime("%Y_%m_%d_%H_%M_%S"))
        self.log.sender = "DATA"
        self.__filename = filename

        # if not os.path.isfile("overwatch_team.db"):
        #     await cls._setup_new_database()
        conn = sqlite3.connect('overwatch_team.db')
        if conn == None:
            self.log.error("Error connecting to database")
            return
        self.__conn = conn
        self.__cursor = conn.cursor()

        outputstr = "Successfully constructed DBService"
        self.log.info(outputstr)
        self.__sr_table_name = "srdata"
        self.__tz_table_name = "tzinfo"
        return self
    # TODO test this, check out UPSERT for sqlite and add queries for tzinfo
    @classmethod
    async def _setup_new_database(cls):
        db_name = "overwatch_team.db"
        self.log.info(f"Setting up new database {db_name}")
        Path(f'./{db_name}').touch()
        conn = sqlite3.connect(db_name)
        if not conn:
            self.log.error("Error connecting to database")
        cursor = conn.cursor()
        self.log.info(f"Successfully connected to database {db_name}")
        # Create srdata table
        query = "CREATE TABLE srdata ( \
                name VARACHAR(128), \
                tank BIGINT, \
                damage BIGINT, \
                support BIGINT, \
                )"
        self.log.info("Creating srdata table")
        self.log.info(f"Query: {query}")
        if not cursor.execute(query):
            self.log.error("Error creating srdata table, create table command not executed")
        
        #Create tzinfo table
        query = "CREATE TABLE tzinfo ( \
            id VARCHAR(255), \
            timezone VARCHAR(255), \
            )"
        self.log.info("Creating tzinfo table")
        self.log.info(f"Query: {query}}")
        if not cursor.execute(query):
            self.log.error("Error creating tzinfo table, create table command not executed")
        
        conn.commit()
        conn.close()

    async def commit_changes(self):
       if self.__conn:
           self.__conn.commit()
           self.__conn.close()
    
    async def register(self, message):
        c = self.__cursor
        person = message.author
        if len(message.mentions) > 0 and "team member" in [y.name.lower() for y in message.author.roles]:
            person = message.mentions[0]
            self.log.info(f"Privileged !register invoked by {message.author} for {person}")
        
        if "based" in [y.name.lower() for y in message.author.roles]:
            outputstr = "{} is already registered. Type `!sr @username` for more".format(person.name)
            await message.channel.send(outputstr)
            self.log.error("[{}] ".format(message.author.name) + outputstr)
            return
        
        query = "INSERT INTO {} (name) VALUES ('{}')".format(self.__sr_table_name, person.name)
        self.log.info(f'Query: {query}')
        if not c.execute(query):
            outputstr = "There's been an error and it has been reported. Please try again, later"
            await message.channel.send(outputstr)
            outputstr = "Error in executing query {}".format(query)
            self.log.error(outputstr)
            return

        outputstr = "Successfully added new database entry for {}\n".format(person.name)
        self.log.info(outputstr)
        
        outputstr += "Please set your SR using `!set <role> <sr>`\n"
        outputstr += "For more commands use `!sr --help`"
        await message.channel.send(outputstr)


    
    async def sr_help(self, message):
        outputstr = "If you're a **new user**, type `!register` to start!\n\n"
        outputstr += "To **check your sr**, type `!sr`\n"
        outputstr += "To **set your sr**, type `!set <role> <sr>`\n"
        outputstr += "To **check the team's sr**, type `!sr -team (-v)---optional`\n"
        await message.channel.send(outputstr)
        outputstr = "To **check someone else's sr**, type `!sr @username`\n"
        outputstr += "To **set someone else's sr (admin)**, type `!set @user <role> <sr>`\n"
        outputstr += "To repeat this message, type `!sr --help`\n"
        outputstr += "For full help on the bot, type `!ineedhealing`\n"
        await message.channel.send(outputstr)
        self.log.info(f"SR help message sent to channel {message.channel}")
    
    async def sr(self, message):
        c = self.__cursor
        if "--help" in message.content.lower() or "-help" in message.content.lower():
            self.log.info(f'Sending SR help message to channel {message.channel}')
            await self.sr_help(message)
            return

        if "-team" in message.content.lower():
            query = "SELECT * FROM {}".format(self.__sr_table_name)
            self.log.info(f"Query: {query}")
            c.execute(query)
            highestList = []
            everyone = c.fetchall()
            for i in everyone:
                high = 0
                for j in i[2:]:
                    if j is None:
                        continue
                    if int(j) > high:
                        high = int(j)
                highestList.append(high)
            team_average = statistics.mean(highestList)
            median = statistics.median(highestList)
            standard_dev = statistics.stdev(highestList)
            outputstr = "**Team Average SR: {:.2f}**\n".format(team_average)
            if "-v" in message.content.lower():
                outputstr += "Median (exact middle) SR: {:.2f}\n".format(median)
                outputstr += "Standard Deviation: {:.2f}\n".format(standard_dev)
            self.log.info("[{}]".format(message.author.name) + outputstr)
            outputstr += "\nPlease note that this is based on the provided data so far. Type !sr --help for commands."
            await message.channel.send(outputstr)
            return
    
        person = message.author.name
        if len(message.mentions) > 0:
            person = message.mentions[0].name
            self.log.info("[{}] invoked !sr for {}".format(message.author.name, person))
        
        query = "SELECT * FROM {} WHERE name  = '{}'".format(self.__sr_table_name, person)
        if not c.execute(query):
            outputstr = "There's been an error and it has been reported. Please try again, later"
            await message.channel.send(outputstr)
            outputstr = "Error in executing query {}".format(query)
            return

        user = c.fetchall()
        if len(user) == 0:
            outputstr = "No results found for {}, please register using `!register`".format(person)
            await message.channel.send(outputstr)
            self.log.error(outputstr)
            return

        user = user[0]
        high = 0
        high_index = 0
        for i in user[1:]:
            if i is not None and int(i) > high:
                high = int(i)
                high_index = user.index(i)
        
        outputstr = "For user **{}**\n".format(person)
        
        outputstr += "**Tank: {}**\n".format(user[1]) if high_index == 1 else "Tank: {}\n".format(user[1])
        outputstr += "**Damage: {}**\n".format(user[2]) if high_index == 2 else "Damage: {}\n".format(user[2])
        outputstr += "**Support: {}**\n".format(user[3]) if high_index == 3 else "Support: {}\n".format(user[3])

        await message.channel.send(outputstr)
        self.log.info(outputstr)
         
    
    async def parse_set_query(self, message):
        args = message.content.split(' ')
        self.log.info(f"Parsing set query for {message.author}")
        try:
            role = args[-2]
        except IndexError:
            outputstr = "Usage: !set {@user} role <sr>"
            self.log.error("[{}]".format(message.author.name) + outputstr)
            outputstr += "\nList of acceptable roles - 'tank', 'dps', 'damage', 'dmg', 'support', 'heals'"
            await message.channel.send(outputstr)
            return []

        roleList = ['tank', 'dps', 'damage', 'dmg', 'support', 'heals']
        
        if not role in roleList:
            outputstr = "Usage: !set {@user} role <sr>"
            self.log.error("{}: ".format(message.author.name) + outputstr)
            outputstr += "\nList of acceptable roles - ['tank', 'dps', 'damage', 'dmg', 'support', 'heals']"
            await message.channel.send(outputstr)
            return []
        
        try:
            if len(args[-1]) != 4:
                outputstr = "Please make sure the SR is a 4 digit number"
                await message.channel.send(outputstr)
                self.log.error(outputstr)
                return []
            newSR = int(args[-1])
        except ValueError:
            outputstr = "Please make sure the SR is written as the last part of the message"
            self.log.error("Invoked by {}: ".format(message.author.name) + outputstr)
            await message.channel.send(outputstr)
            return []
        
        if newSR < 0:
            outputstr = "{}, please make sure the SR is a positive number".format(message.author.name)
            self.log.error(outputstr)
            await message.channel.send(outputstr)
            return []

        return [newSR, role]

    async def set(self, message):
        c = self.__cursor
        
        mentions = message.mentions
        if len(mentions) > 0:
            if "admin" in [y.name.lower() for y in message.author.roles]:
                user = mentions[0]
            else:
                outputstr = "Sorry, {}. You'll need admin permissions to do that".format(message.author.name)
                await message.channel.send(outputstr)
                self.log.error(outputstr)
                return
        else:
            user = message.author
        
        try:
            newSR, role = await self.parse_set_query(message)
        except ValueError:
            return

        person = user.name
        
        query = "SELECT * FROM {} WHERE name = '{}'".format(self.__sr_table_name, person)
        if not c.execute(query):
            outputstr = "There's been an error and it has been reported. Please try again, later"
            await message.channel.send(outputstr)
            outputstr = "Error in executing query {}".format(query)
            self.log.error(outputstr)
            return

        user = c.fetchall()

        if len(user) == 0:
            outputstr = "Can't find any details for {}. If you're not registered, type `!register` to start!".format(person)
            self.log.error(outputstr)
            await message.channel.send(outputstr)
            return

        user = user[0]

        
        if role in ('dps', 'dmg'):
            role = "damage"
        elif role == "heals":
            role = "support"

        query = "UPDATE {} SET {} = {} WHERE name = '{}'".format(self.__sr_table_name, role, newSR, person)
        if not c.execute(query):
            outputstr = "There's been an error and it has been reported. Please try again, later"
            await message.channel.send(outputstr)
            outputstr = "Error in executing query {}".format(query)
            self.log.error(outputstr)
            return
        
        outputstr = "Successfully changed {}'s {} SR to {}".format(person, role, newSR)
        await message.channel.send(outputstr)
        self.log.info(outputstr)
        await self.sr(message)
    
    def get_all_timezones(self):
        c = self.__cursor
        query = "SELECT timezone FROM {}".format(self.__tz_table_name)
        if not c.execute(query):
            return
        timezones = set(c.fetchall())
        
        if len(timezones) == 0:
            self.log.error("Can't find any timezones")
            return
        
        return [i[0] for i in timezones]

    
    def get_sender_timezone(self, author_id):
        c = self.__cursor
        query = "SELECT timezone FROM {} WHERE id = '{}'".format(self.__tz_table_name, author_id)
        self.log.info(f"Query: {query}")
        if not c.execute(query):
            self.log.error("Error executing query")
            return
        timezone = c.fetchall()
        if len(timezone) == 0:
            outputstr = "Can't find any details for {}".format(author_id)
            self.log.error(outputstr)
            return
        return timezone[0][0]

        
