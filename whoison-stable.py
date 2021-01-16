import discord
import datetime
from prettytable import PrettyTable
import random
import asyncio
import copy
from modules.practice import practice



# Currently Running : Bastion
TOKEN = '' #Your token here 

client = discord.Client()
filename = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".log"
globalMap = {} # dict {user : datetime}
START = datetime.datetime.now() # bot start time
numInstr = 0 # number of instructions parsed
numBugs = 0 # number of bugs reported
allgrouped = {} # dict {id : group number}
groupList = [] # list of lists groupList : [ [ users ] ]
smurfList = [] # list of all online smurf accounts

def isGrouped(userID):
    if userID in [*allgrouped]:
        return True
    return False


def validateGroup(message):
    for l in groupList:
        if len(l) == 1:
            allgrouped.pop(l[0])
            groupList.remove(l)

async def ungroup(message, user):
    callerGroup = allgrouped[user]
    groupList[callerGroup].remove(user)
    callerGroup = groupList[callerGroup]
    del allgrouped[user]
    await message.channel.send("{} has been removed from the group".format(user.name))
    validateGroup(message)
    if callerGroup not in groupList:
        await message.channel.send(
            "{}'s group has been destroyed, {} has now been ungrouped".format(
               user.name, callerGroup[0].name))

def writeToFile(outputstr):
    global numInstr
    f = open(filename, "a")
    f.write("[{}]: {}\n".format(datetime.datetime.now(), outputstr))
    f.close()
    numInstr += 1

async def on(message):
    addedPerson = message.author
    mentions = message.mentions
    if len(mentions) > 0 :
        if "admin" in [y.name.lower() for y in message.author.roles]:
            outputstr = "Admin command invoked by {}".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
            for i in mentions:
                globalMap[i] = datetime.datetime.now()
                outputstr = "{} is now online!".format(i.name)
                await message.channel.send(outputstr)
        else:
            outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
            return
    else:
        globalMap[addedPerson] = datetime.datetime.now()        
        outputstr = "{} is now online!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)


async def whoison(message):
    sortedList = sorted(globalMap.items(), key=lambda x: x[1])
    end = datetime.datetime.now()
    if len(sortedList) == 0:
        outputstr = "No one is on at the moment, {}, if you're going online, say \"!on\" to let people know!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)
        return
    for i in sortedList:
        outputstr = "{}".format(i[0].name)
        if i[0] in smurfList:
            outputstr += " (smurf) " 
        outputstr += " has been on for {}".format(str((end - i[1])))
        await message.channel.send(outputstr.split('.')[0])
        writeToFile(outputstr)

async def off(message):
    deletedPerson = message.author
    
    async def turnOff(user):
        try:
            del globalMap[user]
            # Remove from smurfs
            if user in smurfList:
                smurfList.remove(user)
            # Remove from groups
            if isGrouped(user.id):
                await ungroup(message, user)
            return "{} is now offline".format(user.name)
        except KeyError:
            return "{} was not online".format(user.name)

    mentions = message.mentions
    if len(mentions) > 0:
        if "admin" in [y.name.lower() for y in message.author.roles]:
            for i in mentions:
                    outputstr = await turnOff(i)
                    await message.channel.send(outputstr)
                    writeToFile(outputstr)
        else:
            outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
    else:
        outputstr = await turnOff(deletedPerson)
        await message.channel.send(outputstr)
        writeToFile(outputstr)


async def group(message):
    blockedList = []
    acceptedList = []
    callerGroup = None
    mentions = message.mentions
    if len(mentions) == 0:
        await message.channel.send("Usage !group @<user> or [list of users]")
        writeToFile("{} used incorrect group creation syntax".format(message.author.name))
        return
    elif message.author not in [*globalMap]:
        outputstr = "Group Creation Failure: {} is not online. Please type \"!on\" tp set your status as online".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)
        return
    else:
        if isGrouped(message.author.id):
            callerGroup = allgrouped[message.author]
        else:
            newGroup = [message.author]
            groupList.append(newGroup)
            callerGroup = groupList.index(newGroup)
            allgrouped[message.author] = callerGroup
        
        if message.author in mentions:
            mentions.remove(message.author)
        
        for i in mentions:
            if i in [*allgrouped] or i not in [*globalMap]:
                blockedList.append(i.name)
            else:
                acceptedList.append(i.name)
                groupList[callerGroup].append(i)
                allgrouped[i] = callerGroup
        
        validateGroup(message)
        
        if message.author not in [*allgrouped]:
            writeToFile("{} created an invalid group, handled".format(message.author.name))
            await message.channel.send("Group invalid, number of valid members must be at least 2")
        else:
            outputstr = "New Group Created for {}!".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
            if len(acceptedList) > 0:
                outputstr = "The following players were added to the group {}".format(acceptedList).replace('[', '').replace(']', '')
                await message.channel.send(outputstr)
                writeToFile(outputstr)
            if len(blockedList) > 0:
                outputstr = "The following players were not added since they are already grouped or offline, type !ungroup to remove yourself or !on to set your status as online {}".format(
                        blockedList).replace('[', '').replace(']', '')
                await message.channel.send(outputstr)
                writeToFile(outputstr)        

async def destroygroup(message):
    outputstr = "Admin command invoked by {}".format(message.author.name)
    await message.channel.send(outputstr)
    writeToFile(outputstr)
    if len(groupList) == 0:
        outputstr = "There are no active groups!"
        await message.channel.send(outputstr)
        writeToFile(outputstr)
    elif not any(map(str.isdigit, message.content.lower())):
        await message.channel.send("Usage: !destroygroup <group number>.\nPlease take a look at !whoisgrouped for the group number")
        writeToFile("{} invoked command without numbers".format(message.author.name))
    else:
        groupNo = int(message.content.lower().split(' ')[1]) - 1
        
        if groupNo < 0 or groupNo >= len(groupList):
            await message.channel.send("Invalid group number")
            writeToFile("{} invoked command with incorrect number".format(message.author.name))
            return
        ungroupList = [k for k,v in allgrouped.items() if int(v) == groupNo]
        try:
            for i in ungroupList:
                await ungroup(message, i)
        except KeyError as e:
            writeToFile("Error: {}".format(e))

async def bug(message):
    global numBugs
    myID = '<@!317936860393635843>'
    await message.channel.send("Bug Reported, thank you.\n Ping {} for updates".format(myID))
    outputstr = "---------------------------------------BUG REPORTED--------------------------------------------"
    writeToFile(outputstr)
    numBugs += 1



@client.event
async def on_message(message):
    global numInstr
    global numBugs

    if message.author == client.user:
            return

    if "!on" in message.content.lower():
        await on(message)

    if "!smurf" in message.content.lower():
        smurfList.append(message.author)
        if message.author not in [*globalMap]:
            await on(message)
        outputstr = "{} is now smurfing".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

    if message.content.lower() in ["!whoison", "!whoson", "!whoon", "!whothefuckison", "!whotfison"]:
        await whoison(message)

    if "!off" in message.content.lower():
        await off(message)

    #Admin commands

    if "!alloff" in message.content.lower() and "admin" in  [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        allgrouped.clear()
        groupList.clear()
        outputstr = "Admin command invoked by {}, everyone is off! All groups destroyed!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

    # Status Commands
    if "!status" in message.content.lower():
        if message.author.name == "Orisa":
            return
        duration = datetime.datetime.now() - START
        outputstr = "The bot is online and has been running for {}\n".format(str(duration).split('.')[0])
        if "-v" in message.content.lower():
            outputstr += "In this session, \n"
            outputstr += "{} unique instructions have been processed\n".format(numInstr + 1) # +1 for current instruction
            outputstr += "{} unique bugs have been reported\n".format(numBugs)
            # Saving this space for any other meta information people might need
        await message.channel.send(outputstr)
        writeToFile(outputstr)
    
    if "!needhealing" in message.content.lower() or "!ineedhealing" in message.content.lower(): 
        outputstr = "Hi, I'm Orisa, a bot made by Zoid to automate the boring stuff on this server. For a full list of commands and documentation follow the link below \n"
        outputstr += "https://bhavdeepsinghb.github.io/OrisaBot"
        await message.channel.send(outputstr)

    # Grouping
    if "!group" in message.content.lower():
        await group(message)

    if "!ungroup" in message.content.lower():
        if message.author not in [*globalMap]:
            outputstr = "{} is not online, therefore not part of any groups".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        elif message.author not in [*allgrouped]:
            outputstr = "{} was not part of a group".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        else:
           await ungroup(message, message.author)

    if "!whoisgrouped" in message.content.lower():
        if len(groupList) == 0:
            await message.channel.send("There are no active groups, type !group @<user> or [a list of users] to start grouping up!")
        else:
            await message.channel.send("The following is a list of all groups")
            nickList = []
            for i in groupList:
                nickList = []
                for x in i:
                    nickList.append(x.nick if x.nick is not None else x.name)
                await message.channel.send("{}) {}".format(groupList.index(i) + 1, nickList))
        writeToFile("{} invoked whoisgrouped command. Returned {} results".format(message.author.name, len(groupList)))

    # Admin command for destroying groups
    if "!destroygroup" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        await destroygroup(message)
    
    #Practice Command for admins, to avoid spam
    if "!practice" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        await practice(message, globalMap, client)

    # Bug Command to report bugs, marked in the logfile + mentions user 
    if "!bug" in message.content.lower():
        await bug(message)
    
    
    #Misc - won't be written to log files
    if message.content.lower() == "f":
        await message.channel.send("{} has put some respecc on it".format(message.author.name))
    
    if message.content.lower() == "a":
        await message.channel.send("{} has assembled the Avengers!".format(message.author.name))
    
    if message.content.lower() == "x":
        await message.channel.send("{} has assembled the X-Men!".format(message.author.name))


@client.event
async def on_ready():
    print("Ready")


client.run(TOKEN)

