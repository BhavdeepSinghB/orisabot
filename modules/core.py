from modules.utils import writeToFile
import datetime

class CoreService:
    #Variables
    __filename = None
    __globalMap = None
    __allgrouped = None
    __groupList = None
    __smurfList = None
    __notifyDict = None


    @classmethod
    async def construct(cls, filename):
        self = CoreService()

        self.__filename = filename
        self.__globalMap = {}
        self.__allgrouped = {}
        self.__groupList = []
        self.__smurfList = []
        self.__notifyDict = {"All": []}
    
    async def get_online_users(self):
        return self.__globalMap

    async def notify(self, message, user, outputstr):
        # Include "All" since these people must be notified regardless
        efficientTuple = ("All", user)
        for obj in efficientTuple:
            # Check if the user is in notify map
            if obj in self.__notifyDict.keys():
                # if yes, notify each user in the list
                for i in self.__notifyDict[obj]:
                    if not i == user:
                        await i.send(outputstr)
                    # remove user, avoiding spam
                    self.__notifyDict[obj].remove(i)
    
    async def on(self, message):
        addedPerson = message.author
        mentions = message.mentions
        if len(mentions) > 0 :
            if "admin" in [y.name.lower() for y in message.author.roles]:
                outputstr = "Admin command invoked by {}".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(self.__filename, outputstr)
                for i in mentions:
                    self.__globalMap[i] = datetime.datetime.now()
                    outputstr = "{} is now online!".format(i.name)
                    await self.notify(message, i, outputstr)
                    await message.channel.send(outputstr)
                    writeToFile(self.__filename, outputstr)
            else:
                outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(self.__filename, outputstr)
                return
        else:
            self.__globalMap[addedPerson] = datetime.datetime.now()        
            outputstr = "{} is now online!".format(message.author.name)
            await self.notify(message, addedPerson, outputstr)
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)

    async def lmk(self, message):
        notifier = "All"
        if len(message.mentions) > 0:
            notifier = message.mentions[0]
        if notifier in self.__notifyDict.keys():
            self.__notifyDict[notifier].append(message.author)
        else:
            self.__notifyDict[notifier] = [message.author]
        outputstr = "{} will be notified the next time {} goes on".format(message.author.name, notifier.name if len(message.mentions) > 0 else "someone")
        writeToFile(self.__filename, outputstr)
        await message.channel.send(outputstr)

    async def whoison(self, message):
        sortedList = sorted(self.__globalMap.items(), key=lambda x: x[1])
        end = datetime.datetime.now()
        if len(sortedList) == 0:
            outputstr = "No one is on at the moment, {}, if you're going online, say \"!on\" to let people know!".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)
            return
        for i in sortedList:
            outputstr = "{}".format(i[0].name)
            if i[0] in self.__smurfList:
                outputstr += " (smurf) " 
            outputstr += " has been on for {}".format(str((end - i[1])))
            await message.channel.send(outputstr.split('.')[0])
            writeToFile(self.__filename, outputstr)
    
    async def off(self, message):
        deletedPerson = message.author
        
        async def turnOff(user):
            try:
                del self.__globalMap[user]
                # Remove from smurfs
                if user in self.__smurfList:
                    self.__smurfList.remove(user)
                # Remove from groups
                if self.isGrouped(user):
                    await self.ungroup(message, user)
                return "{} is now offline".format(user.name)
            except KeyError:
                return "{} was not online".format(user.name)

        mentions = message.mentions
        if len(mentions) > 0:
            if "admin" in [y.name.lower() for y in message.author.roles]:
                for i in mentions:
                        outputstr = await turnOff(i)
                        await message.channel.send(outputstr)
                        writeToFile(self.__filename, outputstr)
            else:
                outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(self.__filename, outputstr)
        else:
            outputstr = await turnOff(deletedPerson)
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)
    
    async def smurf(self, message):
        if len(message.mentions) > 0 and "admin" in [y.name.lower() for y in message.author.roles]:
            user = message.mentions[0]
        else:
            user = message.author
        self.__smurfList.append(user)
        if user not in [*self.__globalMap]:
            await self.on(message)
        outputstr = "{} is now smurfing".format(user.name)
        await message.channel.send(outputstr)
        writeToFile(self.__filename, outputstr)

    def isGrouped(self, user):
        if user in [*self.__allgrouped]:
            return True
        return False

    def validateGroup(self, message):
        for l in self.__groupList:
            if len(l) == 1:
                self.__allgrouped.pop(l[0])
                self.__groupList.remove(l)

    async def ungroup(self, message, user):
        callerGroup = self.__allgrouped[user]
        self.__groupList[callerGroup].remove(user)
        callerGroup = self.__groupList[callerGroup]
        del self.__allgrouped[user]
        await message.channel.send("{} has been removed from the group".format(user.name))
        self.validateGroup(message)
        if callerGroup not in self.__groupList:
            await message.channel.send(
                "{}'s group has been destroyed, {} has now been ungrouped".format(
                user.name, callerGroup[0].name))
    
    async def ungroup_helper(self, message):
        if message.author not in [*self.__globalMap]:
            outputstr = "{} is not online, therefore not part of any groups".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)
        elif message.author not in [*self.__allgrouped]:
            outputstr = "{} was not part of a group".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)
        else:
           await self.ungroup(message, message.author)

    async def group(self, message):
        blockedList = []
        acceptedList = []
        callerGroup = None
        mentions = message.mentions
        if len(mentions) == 0:
            await message.channel.send("Usage !group @<user> or [list of users]")
            writeToFile(self.__filename, "{} used incorrect group creation syntax".format(message.author.name))
            return
        elif message.author not in [*self.__globalMap]:
            outputstr = "Group Creation Failure: {} is not online. Please type \"!on\" tp set your status as online".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)
            return
        else:
            if self.isGrouped(message.author):
                callerGroup = self.__allgrouped[message.author]
            else:
                newGroup = [message.author]
                self.__groupList.append(newGroup)
                callerGroup = self.__groupList.index(newGroup)
                self.__allgrouped[message.author] = callerGroup
            
            if message.author in mentions:
                mentions.remove(message.author)
            
            for i in mentions:
                if i in [*self.__allgrouped] or i not in [*self.__globalMap]:
                    blockedList.append(i.name)
                else:
                    acceptedList.append(i.name)
                    self.__groupList[callerGroup].append(i)
                    self.__allgrouped[i] = callerGroup
            
            self.validateGroup(message)
            
            if message.author not in [*self.__allgrouped]:
                writeToFile(self.__filename, "{} created an invalid group, handled".format(message.author.name))
                await message.channel.send("Group invalid, number of valid members must be at least 2")
            else:
                outputstr = "New Group Created for {}!".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(self.__filename, outputstr)
                if len(acceptedList) > 0:
                    outputstr = "The following players were added to the group {}".format(acceptedList).replace('[', '').replace(']', '')
                    await message.channel.send(outputstr)
                    writeToFile(self.__filename, outputstr)
                if len(blockedList) > 0:
                    outputstr = "The following players were not added since they are already grouped or offline, type !ungroup to remove yourself or !on to set your status as online {}".format(
                            blockedList).replace('[', '').replace(']', '')
                    await message.channel.send(outputstr)
                    writeToFile(self.__filename, outputstr)

    async def whoisgrouped(self, message):
        if len(self.__groupList) == 0:
            await message.channel.send("There are no active groups, type !group @<user> or [a list of users] to start grouping up!")
        else:
            await message.channel.send("The following is a list of all groups")
            nickList = []
            for i in self.__groupList:
                nickList = []
                for x in i:
                    nickList.append(x.nick if x.nick is not None else x.name)
                await message.channel.send("{}) {}".format(self.__groupList.index(i) + 1, nickList))
        writeToFile(self.__filename, "{} invoked whoisgrouped command. Returned {} results".format(message.author.name, len(self.__groupList)))

    async def destroygroup(self, message):
        outputstr = "Admin command invoked by {}".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(self.__filename, outputstr)
        if len(self.__groupList) == 0:
            outputstr = "There are no active groups!"
            await message.channel.send(outputstr)
            writeToFile(self.__filename, outputstr)
        elif not any(map(str.isdigit, message.content.lower())):
            await message.channel.send("Usage: !destroygroup <group number>.\nPlease take a look at !whoisgrouped for the group number")
            writeToFile(self.__filename, "{} invoked command without numbers".format(message.author.name))
        else:
            groupNo = int(message.content.lower().split(' ')[1]) - 1
            
            if groupNo < 0 or groupNo >= len(self.__groupList):
                await message.channel.send("Invalid group number")
                writeToFile(self.__filename, "{} invoked command with incorrect number".format(message.author.name))
                return
            ungroupList = [k for k,v in self.__allgrouped.items() if int(v) == groupNo]
            try:
                for i in ungroupList:
                    await self.ungroup(message, i)
            except KeyError as e:
                writeToFile(self.__filename, "Error: {}".format(e))
    
    async def alloff(self, message): 
        self.__globalMap.clear()
        self.__allgrouped.clear()
        self.__groupList.clear()
        outputstr = "Admin command invoked by {}, everyone is off! All groups destroyed!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(self.__filename, outputstr)