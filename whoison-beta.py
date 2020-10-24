import discord
import datetime
from prettytable import PrettyTable
import random
import asyncio
import copy
from modules.practice import practice
from modules.utils import *


# Currently Running : Orisa
TOKEN = '#' #Your token here 

client = discord.Client()
filename = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".log"
globalMap = {}
START = datetime.datetime.now()
numInstr = 0
numBugs = 0
allgrouped = {}
groupList = []


def isGrouped(userID):
    if userID in [*allgrouped]:
        return True
    return False


def validateGroup(message):
    for l in groupList:
        if len(l) <= 1:
            allgrouped.pop(getID(l[0], message))
            groupList.remove(l)

async def ungroup(message, userid):
    user = getUser(userid, message)
    callerGroup = allgrouped[userid]
    groupList[callerGroup].remove(user)
    callerGroup = groupList[callerGroup]
    del allgrouped[userid]
    await message.channel.send("{} has been removed from the group".format(user))
    validateGroup(message)
    if callerGroup not in groupList:
        await message.channel.send(
            "{}'s group has been destroyed, {} has now been ungrouped".format(
               user, callerGroup[0]))

def writeToFile(outputstr):
    global numInstr
    f = open(filename, "a")
    f.write("[{}]: {}\n".format(datetime.datetime.now(), outputstr))
    f.close()
    numInstr += 1

async def on(message):
    addedPersonID = message.author.id
    if message.author.name == "Orisa":
        return
    if "@" in message.content.lower():
        if "admin" in [y.name.lower() for y in message.author.roles]:
            addedPersonID = message.content.split("@")[1]
            addedPersonID = formatID(addedPersonID)
            outputstr = "Admin command invoked by {}".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        else:
            outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
            return
    globalMap[int(addedPersonID)] = datetime.datetime.now()
    outputstr = "{} is now online!".format(getUser(addedPersonID, message))
    await message.channel.send(outputstr)

async def whoison(message):
    if message.author.name == "Orisa":
            return
    sortedList = sorted(globalMap.items(), key=lambda x: x[1])
    end = datetime.datetime.now()
    if len(sortedList) == 0:
        outputstr = "No one is on at the moment, {}, if you're going online, say \"!on\" to let people know!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)
        return
    for i in sortedList:
        outputstr = "{} has been on for {}".format(getUser(i[0], message), str((end - i[1])))
        await message.channel.send(outputstr.split('.')[0])
        writeToFile(outputstr)

async def off(message):
    deletedPersonID = message.author.id
    if message.author.name == "Orisa":
        return
    if "@" in message.content.lower():
        if "admin" in [y.name.lower() for y in message.author.roles]:
            deletedPersonID = message.content.split("@")[1]
            deletedPersonID = formatID(deletedPersonID)
            outputstr = "Admin command invoked by {}".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        else:
            outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(
                message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
            return
    try:
        del globalMap[int(deletedPersonID)]
        outputstr = "{} is now offline".format(getUser(deletedPersonID, message))
        await message.channel.send(outputstr)
        writeToFile(outputstr)
    except KeyError:
        outputstr = "{} was not online".format(getUser(deletedPersonID, message))
        await message.channel.send(outputstr)
        writeToFile(outputstr)
    # If user was in any existing group, kick em out
    if isGrouped(deletedPersonID):
        await ungroup(message, deletedPersonID)

async def group(message):
    if message.author.name == "Orisa":
            return
    blockedList = []
    acceptedList = []
    callerGroup = None
    if '@' not in message.content.lower():
        await message.channel.send("Usage !group @<user> or [list of users]")
        writeToFile("{} used incorrect group creation syntax".format(message.author.name))
        return
    elif message.author.id not in [*globalMap]:
        outputstr = "Group Creation Failure: {} is not online. Please type \"!on\" tp set your status as online".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)
        return
    else:
        if isGrouped(message.author.id):
            callerGroup = allgrouped[message.author.id]
        else:
            newGroup = [message.author.name]
            groupList.append(newGroup)
            callerGroup = groupList.index(newGroup)
            allgrouped[message.author.id] = callerGroup
        textList = message.content.lower().split('@')[1:]
        IDList = [int(formatID(i)) for i in textList]
        if message.author.id in IDList:
            IDList.remove(message.author.id)
        for i in IDList:
            if int(i) in [*allgrouped] or int(i) not in [*globalMap]:
                blockedList.append(getUser(int(i), message))
            else:
                acceptedList.append(getUser(int(i), message))
                groupList[callerGroup].append(getUser(int(i), message))
                allgrouped[i] = callerGroup
        validateGroup(message)
        if message.author.id not in [*allgrouped]:
            writeToFile("{} created an invalid group, handled".format(message.author.name))
            await message.channel.send("group invalid, number of valid members must be at least 2")
        else:
            outputstr = "New Group Created for {}!".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
            if len(acceptedList) > 0:
                outputstr = "The following players were added to the group {}".format(acceptedList)
                await message.channel.send(outputstr)
                writeToFile(outputstr)
            if len(blockedList) > 0:
                outputstr = "The following players were not added since they are already grouped or offline, type !ungroup to remove yourself or !on to set your status as online {}".format(
                        blockedList)
                await message.channel.send(outputstr)
                writeToFile(outputstr)

async def destroygroup(message):
    if message.author.name == "Orisa":
            return
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

    if "!on" in message.content.lower():
        await on(message)


    if message.content.lower() in ["!whoison", "!whoson", "!whoon", "!whothefuckison", "!whotfison"]:
        await whoison(message)

    if "!off" in message.content.lower():
        await off(message)

    #Admin commands
    if "!allon" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        for member in message.guild.members:
            if member.name == "Orisa" or member.name == "Doom":
                continue
            globalMap[member.id] = datetime.datetime.now()
        outputstr = "Admin command invoked by {}, everyone is on!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

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
    
    if "!help" in message.content.lower(): 
        outputstr = "Hi, I'm Orisa, a bot made by Zoid to automate the boring stuff on this server. For a full list of commands and documentation follow the link below \n"
        outputstr += "https://bhavdeepsinghb.github.io/OrisaBot"
        await message.channel.send(outputstr)

    # Grouping
    if "!group" in message.content.lower():
        await group(message)

    if "!ungroup" in message.content.lower():
        if message.author.name == "Orisa":
            return
        if message.author.id not in [*globalMap]:
            outputstr = "{} is not online, therefore not part of any groups".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        elif message.author.id not in [*allgrouped]:
            outputstr = "{} was not part of a group".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        else:
           await ungroup(message, message.author.id)

    if "!whoisgrouped" in message.content.lower():
        if len(groupList) == 0:
            await message.channel.send("There are no active groups, type !group @<user> or [a list of users] to start grouping up!")
        else:
            await message.channel.send("The following is a list of all groups")
            for i in groupList:
                await message.channel.send("{}) {}".format(groupList.index(i) + 1, i))
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

    if "!" in message.content.lower() and "cute" in message.content.lower():
        unformattedName = message.content.lower().split('cute')[0][1:]
        
        if unformattedName.lower() == "taco":
            await message.channel.send("Taco is no longer ugly")
            return
        elif unformattedName.lower() == "cum":
            await message.channel.send("Cum is no longer ugly")
            return
        elif unformattedName.lower() == "evixx":
            await message.channel.send("Evixx was never ugly!")
            return
        elif unformattedName.lower() == "pants":
            await message.channel.send("YOU DARE TRY TO IMPLY THAT OUR LORD AND SAVIOR IS UGLY?!")
            return 
        
        for member in message.guild.members:
            if unformattedName.lower() in str(member.name).lower():
                if str(member.name) in ['Dj_RealMeal', 'trippymcgee', 'Ibonal (E-Bot)']:
                    await message.channel.send("{} was never ugly!".format(member.name))
                    return
                await message.channel.send("{} is no longer ugly".format(member.name))
                return
        
        await message.channel.send("Idk who you're talking about but you, {}, are very cute".format(message.author.name))
        



@client.event
async def on_ready():
    print("Ready")


client.run(TOKEN)

