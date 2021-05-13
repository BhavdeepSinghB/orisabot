import discord, datetime, random, asyncio, copy, threading, time
from modules.practice import practice
from modules.utils import writeToFile
from discord.utils import get
from discord import NotFound
from modules.tables import DBService
from config import ORISA_TOKEN


# Current Version : Orisa 1.2.2
# Bot Configuration
TOKEN = ORISA_TOKEN #Your token here 
client = discord.Client()
filename = "/tmp/" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".log"
globalMap = {} # dict {user : datetime}
START = datetime.datetime.now() # bot start time
numInstr = 0 # number of instructions parsed
numBugs = 0 # number of bugs reported
allgrouped = {} # dict {id : group number}
groupList = [] # list of lists groupList : [ [ users ] ]
smurfList = [] # list of all online smurf accounts
dbservice = DBService() # instance of DBService class
notifyDict = {"All": []} # Dict user object : list of user objects that want to be notified for key



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

async def notify(message, user, outputstr):
    # Include "All" since these people must be notified regardless
    efficientTuple = ("All", user)
    for obj in efficientTuple:
        # Check if the user is in notify map
        if obj in notifyDict.keys():
            # if yes, notify each user in the list
            for i in notifyDict[obj]:
                if not i == user:
                    await i.send(outputstr)
                # remove user, avoiding spam
                notifyDict[obj].remove(i)

async def on(message):
    addedPerson = message.author
    mentions = message.mentions
    if len(mentions) > 0 :
        if "admin" in [y.name.lower() for y in message.author.roles]:
            outputstr = "Admin command invoked by {}".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(filename, outputstr)
            for i in mentions:
                globalMap[i] = datetime.datetime.now()
                outputstr = "{} is now online!".format(i.name)
                await notify(message, i, outputstr)
                await message.channel.send(outputstr)
                writeToFile(filename, outputstr)
        else:
            outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(filename, outputstr)
            return
    else:
        globalMap[addedPerson] = datetime.datetime.now()        
        outputstr = "{} is now online!".format(message.author.name)
        await notify(message, addedPerson, outputstr)
        await message.channel.send(outputstr)
        writeToFile(filename, outputstr)

async def lmk(message):
    notifier = "All"
    if len(message.mentions) > 0:
        notifier = message.mentions[0]
    if notifier in notifyDict.keys():
        notifyDict[notifier].append(message.author)
    else:
        notifyDict[notifier] = [message.author]
    outputstr = "{} will be notified the next time {} goes on".format(message.author.name, notifier.name if len(message.mentions) > 0 else "someone")
    writeToFile(filename, outputstr)
    await message.channel.send(outputstr)

async def whoison(message):
    sortedList = sorted(globalMap.items(), key=lambda x: x[1])
    end = datetime.datetime.now()
    if len(sortedList) == 0:
        outputstr = "No one is on at the moment, {}, if you're going online, say \"!on\" to let people know!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(filename, outputstr)
        return
    for i in sortedList:
        outputstr = "{}".format(i[0].name)
        if i[0] in smurfList:
            outputstr += " (smurf) " 
        outputstr += " has been on for {}".format(str((end - i[1])))
        await message.channel.send(outputstr.split('.')[0])
        writeToFile(filename, outputstr)

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
                    writeToFile(filename, outputstr)
        else:
            outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(filename, outputstr)
    else:
        outputstr = await turnOff(deletedPerson)
        await message.channel.send(outputstr)
        writeToFile(filename, outputstr)


async def group(message):
    blockedList = []
    acceptedList = []
    callerGroup = None
    mentions = message.mentions
    if len(mentions) == 0:
        await message.channel.send("Usage !group @<user> or [list of users]")
        writeToFile(filename, "{} used incorrect group creation syntax".format(message.author.name))
        return
    elif message.author not in [*globalMap]:
        outputstr = "Group Creation Failure: {} is not online. Please type \"!on\" tp set your status as online".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(filename, outputstr)
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
            writeToFile(filename, "{} created an invalid group, handled".format(message.author.name))
            await message.channel.send("Group invalid, number of valid members must be at least 2")
        else:
            outputstr = "New Group Created for {}!".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(filename, outputstr)
            if len(acceptedList) > 0:
                outputstr = "The following players were added to the group {}".format(acceptedList).replace('[', '').replace(']', '')
                await message.channel.send(outputstr)
                writeToFile(filename, outputstr)
            if len(blockedList) > 0:
                outputstr = "The following players were not added since they are already grouped or offline, type !ungroup to remove yourself or !on to set your status as online {}".format(
                        blockedList).replace('[', '').replace(']', '')
                await message.channel.send(outputstr)
                writeToFile(filename, outputstr)        

async def destroygroup(message):
    outputstr = "Admin command invoked by {}".format(message.author.name)
    await message.channel.send(outputstr)
    writeToFile(filename, outputstr)
    if len(groupList) == 0:
        outputstr = "There are no active groups!"
        await message.channel.send(outputstr)
        writeToFile(filename, outputstr)
    elif not any(map(str.isdigit, message.content.lower())):
        await message.channel.send("Usage: !destroygroup <group number>.\nPlease take a look at !whoisgrouped for the group number")
        writeToFile(filename, "{} invoked command without numbers".format(message.author.name))
    else:
        groupNo = int(message.content.lower().split(' ')[1]) - 1
        
        if groupNo < 0 or groupNo >= len(groupList):
            await message.channel.send("Invalid group number")
            writeToFile(filename, "{} invoked command with incorrect number".format(message.author.name))
            return
        ungroupList = [k for k,v in allgrouped.items() if int(v) == groupNo]
        try:
            for i in ungroupList:
                await ungroup(message, i)
        except KeyError as e:
            writeToFile(filename, "Error: {}".format(e))

async def bug(message):
    global numBugs
    myID = '<@!317936860393635843>'
    await message.channel.send("Bug Reported, thank you.\n Ping {} for updates".format(myID))
    outputstr = "---------------------------------------BUG REPORTED--------------------------------------------"
    writeToFile(filename, outputstr)
    numBugs += 1

async def smurf(message):
    if len(message.mentions) > 0 and "admin" in [y.name.lower() for y in message.author.roles]:
        user = message.mentions[0]
    else:
        user = message.author
    smurfList.append(user)
    if user not in [*globalMap]:
        await on(message)
    outputstr = "{} is now smurfing".format(user.name)
    await message.channel.send(outputstr)
    writeToFile(filename, outputstr)


@client.event
async def on_message(message):
    global numInstr
    global numBugs
    global dbservice

    if message.author == client.user:
            return

    if "!on" in message.content.lower():
        await on(message)

    if "!smurf" in message.content.lower():
        await smurf(message)

    if message.content.lower() in ["!whoison", "!whoson", "!whoon", "!whothefuckison", "!whotfison"]:
        await whoison(message)

    if "!off" in message.content.lower():
        await off(message)

    if "!lmk" in message.content.lower():
        await lmk(message)

    #Admin commands

    if "!alloff" in message.content.lower() and "admin" in  [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        allgrouped.clear()
        groupList.clear()
        outputstr = "Admin command invoked by {}, everyone is off! All groups destroyed!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(filename, outputstr)

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
        writeToFile(filename, outputstr)
    
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
            writeToFile(filename, outputstr)
        elif message.author not in [*allgrouped]:
            outputstr = "{} was not part of a group".format(message.author.name)
            await message.channel.send(outputstr)
            writeToFile(filename, outputstr)
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
        writeToFile(filename, "{} invoked whoisgrouped command. Returned {} results".format(message.author.name, len(groupList)))

    # Admin command for destroying groups
    if "!destroygroup" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        await destroygroup(message)
    
    #Practice Command for admins, to avoid spam
    if "!practice" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        await practice(message, globalMap, client)

    # Bug Command to report bugs, marked in the logfile + mentions user 
    if "!bug" in message.content.lower():
        await bug(message)
    
    
    if "!sr" in message.content.lower():
        if "team member" in [y.name.lower() for y in message.author.roles]:
            await dbservice.sr(message)
        else:
            outputstr = "Sorry, {}. You'll have to be a team member to do that".format(message.author.name)
            await message.channel.send(outputstr)
    
    if "!set" in message.content.lower():
        if "team member" in [y.name.lower() for y in message.author.roles]:
            await dbservice.set(message)
        else:
            outputstr = "Sorry, {}. You'll have to be a team member to do that"

    if "!register" in message.content.lower():
        if "team member" in [y.name.lower() for y in message.author.roles]:
            await dbservice.register(message)
        else:
            outputstr = "Sorry, {}. You'll have to be a team member to do that"


    #Misc - won't be written to log files
    if message.content.lower() == "f":
        await message.channel.send("{} has put some respecc on it".format(message.author.name))
    
    if message.content.lower() == "a":
        await message.channel.send("{} has assembled the Avengers!".format(message.author.name))
    
    if message.content.lower() == "x":
        await message.channel.send("{} has assembled the X-Men!".format(message.author.name))

async def remove_reaction_async(message, user):
    while(len(message.reactions) > 1):
        time.sleep(5)
        await message.remove_reaction('✅', user)

def remove_reaction_sync(message, user):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(remove_reaction_async(message, user))
    loop.close()

@client.event
async def on_ready():
    print("Live")
    global dbservice
    global filename

    dbservice = await DBService.construct(filename)
    
    channelID = 800499934365220864 # welcome
    channel = client.get_channel(channelID)
    roleID = 800501133642170388 # friend
    role = get(client.guilds[0].roles, id=roleID)
    message = await channel.send("React to this message with ✅ to accept the rules and access the server")
    
    def check(reaction, user):
            return str(reaction.emoji) == '✅' and user != message.author
    
    while True:
        await message.add_reaction('✅')
        user = (await client.wait_for('reaction_add', check=check))[1]    
        try:
            await message.remove_reaction('✅', user)
        except NotFound:
            writeToFile(filename, "Error, message not found")
            _thread = threading.Thread(target=remove_reaction_sync, args=(message, user))
            _thread.start
        finally:
            await user.add_roles(role)
            outputstr = "Gave the {} role to {}".format(role.name, user.name)
            writeToFile(filename, outputstr)
    

client.run(TOKEN)

