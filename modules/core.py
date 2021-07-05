from modules.logging_service import LoggingService
import copy
import datetime

class CoreService:
    #Variables
    __filename = None
    __globalMap = None
    __allgrouped = None
    __groupList = None
    __smurfList = None
    __notifyDict = None
    log = None


    @classmethod
    async def construct(cls, filename, config={}, guild=None, log=None):
        self = CoreService()
        if log:
            self.log = copy.copy(log)
        else:
            self.log = LoggingService(filename=datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
        self.log.sender = "CORE"
        self.__globalMap = {}
        if config.get("globalMap", False) and guild:
            self.log.info("Constructing core from backup")
            config_dict = config['globalMap']
            for i in config_dict.keys():
                member = guild.get_member(int(i))
                if not member:
                    # Log this failure
                    continue
                try:
                    self.__globalMap[member] = datetime.datetime.fromisoformat(config_dict[i])
                except TypeError:
                    # Log this
                    self.__globalMap[member] = datetime.datetime.now()
        self.__allgrouped = {}
        self.__groupList = []
        self.__smurfList = []
        if config.get("smurfList", False) and guild:
            self.log.info("Constructing smurfList from backup")
            self.__smurfList = [guild.get_member(i) for i in config["smurfList"]]
        self.__notifyDict = {"All": []}
        if config.get("notifyDict", False) and guild:
            self.log.info("Constructing notifyDict from backup")
            config_dict = config['notifyDict']
            for i in config_dict.keys():
                if i == "All":
                    self.__notifyDict[i] = [guild.get_member(x) for x in config_dict[i]]
                    continue
                member = guild.get_member(int(i))
                if not member:
                    continue
                self.__notifyDict[member] =[guild.get_member(x) for x in config_dict[i]]
        outputstr = "Successfully constructed Core Service"
        self.log.info(outputstr)
        return self

    @property
    def notif_data(self):
        self.log.info('Returning notifyDict')
        return self.__notifyDict

    @property
    def smurfs(self):
        self.log.info('Returning smurfList')
        return self.__smurfList
    
    def get_online_users(self):
        self.log.info('Returning globalMap')
        return copy.copy(self.__globalMap)

    async def notify(self, message, user, outputstr):
        # Include "All" since these people must be notified regardless
        efficientTuple = ("All", user)
        for obj in efficientTuple:
            # Check if the user is in notify map
            if obj in self.__notifyDict.keys():
                # if yes, notify each user in the list
                for i in self.__notifyDict[obj]:
                    if not i == user:
                        self.log.info(f'Notifying {i}')
                        await i.send(outputstr)
                    # remove user, avoiding spam
                    self.__notifyDict[obj].remove(i)
    
    async def on(self, message=None, role=None, user=None, channel=None):

        async def turnOn(user, channel=None):
            self.__globalMap[user] = datetime.datetime.now()
            self.log.info(f"Added {user} to globalMap")
            if role != None:
                await user.add_roles(role)
                self.log.info(f"Gave {user} the {role} role")
            outputstr = "{} is now online".format(user.name)
            self.log.info(f"Notifying users about {user}")
            await self.notify(message, user, outputstr)
            if channel: 
                await channel.send(outputstr)
            self.log.info(outputstr)
        
        if user:
            await turnOn(user)
            self.log.info(f"Direct on issued for {user.name}")
            return True

        addedPerson = message.author
        mentions = message.mentions
        if len(mentions) > 0:
            if "team member" in [y.name.lower() for y in message.author.roles]:
                self.log.info(f"Privileged !on invoked by {message.author}")
                for i in mentions:
                    await turnOn(i, message.channel)
            else:
                outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or onfor other users"\
                    .format(message.author.name)
                await message.channel.send(outputstr)
                self.log.info(outputstr)
                return
        else:
            await turnOn(addedPerson, message.channel)

    # TODO ; Add role for notify and change logic to mention role instead of DM
    async def lmk(self, message, role=None):
        notifier = "All"
        if len(message.mentions) > 0:
            notifier = message.mentions[0]
        if notifier in self.__notifyDict.keys():
            self.__notifyDict[notifier].append(message.author)
        else:
            self.__notifyDict[notifier] = [message.author]
        outputstr = "{} will be notified the next time {} goes on".format(message.author.name, notifier.name if len(message.mentions) > 0 else "someone")
        self.log.info(outputstr)
        await message.channel.send(outputstr)

    async def whoison(self, message):
        sortedList = sorted(self.__globalMap.items(), key=lambda x: x[1])
        end = datetime.datetime.now()
        if len(sortedList) == 0:
            outputstr = "No one is on at the moment, {}, if you're going online, say \"!on\" to let people know!".format(message.author.name)
            await message.channel.send(outputstr)
            self.log.info(outputstr)
            return
        for i in sortedList:
            outputstr = "{}".format(i[0].nick if i[0].nick is not None else i[0].name)
            if i[0] in self.__smurfList:
                outputstr += " (smurf) " 
            outputstr += " has been on for {}".format(str((end - i[1])))
            await message.channel.send(outputstr.split('.')[0])
            self.log.info(outputstr)
    
    async def __is_online__(self, user):
        is_online = user in self.__globalMap.keys()
        self.log.info(f"is_online {user} - {is_online}")
        return is_online
    
    async def off(self, message=None, role=None, user=None):
    
        async def turnOff(user):
            try:
                self.log.info(f'Removing {user} from globalMap')
                del self.__globalMap[user]
                # Remove from smurfs
                if user in self.__smurfList:
                    self.log.info(f'Removing {user} from smurfList')
                    self.__smurfList.remove(user)
                # Remove from groups
                if self.isGrouped(user):
                    self.log.info(f'Removing {user} from group')
                    await self.ungroup(message, user)
                if role != None:
                    self.log.info(f'Removing {role} from {user}')
                    await user.remove_roles(role)
                return "{} is now offline".format(user.name)
            except KeyError:
                self.log.warn(f'[!off] {user} was not online')
                return "{} was not online".format(user.name)

        if user:
            self.log.info(f"Direct turnoff issued for {user.name}")
            return await turnOff(user)
            

        deletedPerson = message.author
        mentions = message.mentions
        if len(mentions) > 0:
            if "team member" in [y.name.lower() for y in message.author.roles]:
                self.log.info(f'Privileged !off invoked by {message.author} for {message.mentions}')
                for i in mentions:
                    outputstr = await turnOff(i)
                    await message.channel.send(outputstr)
                    self.log.info(outputstr)
            else:
                outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
                await message.channel.send(outputstr)
                self.log.warn(outputstr)
        else:
            outputstr = await turnOff(deletedPerson)
            await message.channel.send(outputstr)
            self.log.info(outputstr)
    
    async def smurf(self, message, role=None):
        if len(message.mentions) > 0 and "admin" in [y.name.lower() for y in message.author.roles]:
            user = message.mentions[0]
            self.log.info(f'Privileged !smurf invoked by {message.author} for {user}')
        else:
            user = message.author
        self.log.info(f'Adding {user} to smurfList')
        self.__smurfList.append(user)
        if user not in [*self.__globalMap]:
            self.log.info(f'{user} not was not online, turning !on')
            await self.on(message)
        outputstr = "{} is now smurfing".format(user.name)
        await message.channel.send(outputstr)
        self.log.info(outputstr)

    def isGrouped(self, user):
        if user in [*self.__allgrouped]:
            self.log.info(f'(isGrouped) yes {user}')
            return True
        self.log.info(f'(isGrouped) no {user}')
        return False

    def validateGroup(self, message):
        for l in self.__groupList:
            if len(l) == 1:
                self.log.info(f'Invalid group {l}')
                self.__allgrouped.pop(l[0])
                self.__groupList.remove(l)

    async def ungroup(self, message, user):
        self.log.info(f'Ungroupping {user}')
        callerGroup = self.__allgrouped[user]
        self.log.info(f'Removing from group {callerGroup}')
        self.__groupList[callerGroup].remove(user)
        self.log.info(f'Removed {user} from groupList')
        callerGroup = self.__groupList[callerGroup]
        del self.__allgrouped[user]
        self.log.info(f'Removed {user} from allgrouped')
        await message.channel.send("{} has been removed from the group".format(user.name))
        self.log.info(f'Validating group')
        self.validateGroup(message)
        if callerGroup not in self.__groupList:
            self.log.info('Invalid group removed successfully')
            await message.channel.send(
                "{}'s group has been destroyed, {} has now been ungrouped".\
                    format(user.name, callerGroup[0].name))
    
    async def ungroup_helper(self, message):
        if message.author not in [*self.__globalMap]:
            outputstr = "{} is not online, therefore not part of any groups".format(message.author.name)
            await message.channel.send(outputstr)
            self.log.warn(outputstr)
        elif message.author not in [*self.__allgrouped]:
            outputstr = "{} was not part of a group".format(message.author.name)
            await message.channel.send(outputstr)
            self.log.warn(outputstr)
        else:
            await self.ungroup(message, message.author)

    async def group(self, message):
        blockedList = []
        acceptedList = []
        callerGroup = None
        mentions = message.mentions
        self.log.info(f'Group {message.author} with {mentions}')
        if len(mentions) == 0:
            await message.channel.send("Usage !group @<user> or [list of users]")
            self.log.error("{} used incorrect group creation syntax".format(message.author.name))
            return
        elif message.author not in [*self.__globalMap]:
            outputstr = "Group Creation Failure: {} is not online. Please type \"!on\" tp set your status as online".format(message.author.name)
            await message.channel.send(outputstr)
            self.log.error(outputstr)
            return
        else:
            if self.isGrouped(message.author):
                callerGroup = self.__allgrouped[message.author]
                self.log.info(f"{message.author}'s group number: {callerGroup}")
            else:
                self.log.info(f'Creating new group for {message.author}')
                newGroup = [message.author]
                self.__groupList.append(newGroup)
                callerGroup = self.__groupList.index(newGroup)
                self.__allgrouped[message.author] = callerGroup
                self.log.info(f'New group for {message.author} created')
            
            if message.author in mentions:
                self.log.info(f'Message contains author, removing')
                mentions.remove(message.author)
            
            for i in mentions:
                if i in [*self.__allgrouped] or i not in [*self.__globalMap]:
                    self.log.info(f'Invalid user: {i} not added to group')
                    blockedList.append(i.name)
                else:
                    self.log.info(f'Valid user: {i} added to group')
                    acceptedList.append(i.name)
                    self.__groupList[callerGroup].append(i)
                    self.__allgrouped[i] = callerGroup
            
            self.log.info("Validating group")
            self.validateGroup(message)
            
            if message.author not in [*self.__allgrouped]:
                self.log.info("{} created an invalid group".format(message.author.name))
                await message.channel.send("Group invalid, number of valid members must be at least 2")
            else:
                outputstr = "New Group Created for {}!".format(message.author.name)
                await message.channel.send(outputstr)
                self.log.info(outputstr)
                if len(acceptedList) > 0:
                    outputstr = "The following players were added to the group {}".format(acceptedList).replace('[', '').replace(']', '')
                    await message.channel.send(outputstr)
                    self.log.info(outputstr)
                if len(blockedList) > 0:
                    outputstr = "The following players were not added since they are already grouped or offline, type !ungroup to remove yourself or !on to set your status as online {}".\
                        format(blockedList).replace('[', '').replace(']', '')
                    await message.channel.send(outputstr)
                    self.log.warn(outputstr)

    async def whoisgrouped(self, message):
        if len(self.__groupList) == 0:
            self.log.info('No active groups')
            await message.channel.send("There are no active groups, type !group @<user> or [a list of users] to start grouping up!")
        else:
            await message.channel.send("The following is a list of all groups")
            nickList = []
            for i in self.__groupList:
                nickList = []
                for x in i:
                    nickList.append(x.nick if x.nick is not None else x.name)
                await message.channel.send("{}) {}".format(self.__groupList.index(i) + 1, nickList))
        self.log.info("{} invoked whoisgrouped command. Returned {} results".format(message.author.name, len(self.__groupList)))

    async def destroygroup(self, message):
        outputstr = "Privileged command invoked by {}".format(message.author.name)
        await message.channel.send(outputstr)
        self.log.info(outputstr)
        if len(self.__groupList) == 0:
            outputstr = "There are no active groups!"
            await message.channel.send(outputstr)
            self.log.error(outputstr)
        elif not any(map(str.isdigit, message.content.lower())):
            await message.channel.send("Usage: !destroygroup <group number>.\nPlease take a look at !whoisgrouped for the group number")
            self.log.error("{} invoked command without numbers".format(message.author.name))
        else:
            groupNo = int(message.content.lower().split(' ')[1]) - 1
            
            if groupNo < 0 or groupNo >= len(self.__groupList):
                await message.channel.send("Invalid group number")
                self.log.error("{} invoked command with incorrect number".format(message.author.name))
                return
            ungroupList = [k for k,v in self.__allgrouped.items() if int(v) == groupNo]
            try:
                for i in ungroupList:
                    await self.ungroup(message, i)
            except KeyError as e:
                self.log.error("Error: {}".format(e))
    
    async def alloff(self, message): 
        self.__globalMap.clear()
        self.__allgrouped.clear()
        self.__groupList.clear()
        outputstr = "Privileged command invoked by {}, everyone is off! All groups destroyed!".format(message.author.name)
        await message.channel.send(outputstr)
        self.log.info(outputstr)