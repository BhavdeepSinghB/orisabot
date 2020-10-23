import discord
import datetime
from prettytable import PrettyTable
import random
import asyncio
import copy

# Currently Running : Off
TOKEN = '#' #Your token here 

client = discord.Client()
filename = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".log"
globalMap = {}
START = datetime.datetime.now()
numInstr = 0
allgrouped = {}
groupList = []

CONTROL = ['Busan', 'Ilios', 'Lijang Tower', 'Nepal', 'Oasis']
ASSAULT = ['Hanamura', 'Temple of Anubis', 'Volskaya Industries']
ESCORTHYB = ['Dorado', 'Havana', 'Junkertown', 'Rialto', 'Route 66', 'Watchpoint Gibraltar', 'Blizzard World', 'Eichenwalde', 'Hollywood', 'King\'s Row', 'Numbani']

def formatID(unformattedID):
    if str(unformattedID[0]) == '!':
        unformattedID = unformattedID.lstrip('!')
    for i in unformattedID:
        if i in ['>', '<', '!', ' ']:
            unformattedID = unformattedID.replace(i, '')
    return unformattedID


def getID(name, message):
    for member in message.guild.members:
        if name == str(member.name):
            return member.id
    return "None"


def getUser(id, message):
    for member in message.guild.members:
        if int(id) == int(member.id):
            return member.name
    return "None"


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


@client.event
async def on_message(message):
    global numInstr
    if "!on" in message.content.lower():
        addedPerson = message.author.name
        if message.author.name == "Orisa":
            return
        if "@" in message.content.lower():
            if "admin" in [y.name.lower() for y in message.author.roles]:
                addedPersonID = message.content.split("@")[1]
                if str(addedPersonID[0]) == '!':
                    addedPersonID = addedPersonID.lstrip('!')
                addedPersonID = addedPersonID.rstrip('>')
                outputstr = "Admin command invoked by {}".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(outputstr)
                for member in message.guild.members:
                    if addedPersonID == str(member.id):
                        addedPerson = member.name
            else:
                outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(outputstr)
                return
        globalMap[addedPerson] = datetime.datetime.now()
        outputstr = "{} is now online!".format(addedPerson)
        await message.channel.send(outputstr)
        writeToFile(outputstr)


    if message.content.lower() in ["!whoison", "!whoson", "!whoon", "!whothefuckison", "!whotfison"]:
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
            outputstr = "{} has been on for {}".format(i[0], str((end - i[1])))
            await message.channel.send(outputstr.split('.')[0])
            writeToFile(outputstr)

    if "!off" in message.content.lower():
        deletedPerson = message.author.name
        deletedPersonID = message.author.id
        if message.author.name == "Orisa":
            return
        if "@" in message.content.lower():
            if "admin" in [y.name.lower() for y in message.author.roles]:
                deletedPersonID = message.content.split("@")[1]
                if str(deletedPersonID[0]) == '!':
                    deletedPersonID = deletedPersonID.lstrip('!')
                deletedPersonID = deletedPersonID.rstrip('>')
                outputstr = "Admin command invoked by {}".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(outputstr)
                deletedPerson = getUser(deletedPersonID, message)
            else:
                outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(
                    message.author.name)
                await message.channel.send(outputstr)
                writeToFile(outputstr)
                return
        try:
            del globalMap[deletedPerson]
            outputstr = "{} is now offline".format(deletedPerson)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        except KeyError:
            outputstr = "{} was not online".format(deletedPerson)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
        # If user was in any existing group, kick em out
        if isGrouped(deletedPersonID):
            await ungroup(message, deletedPersonID)

    #Admin commands
    if "!allon" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        for member in message.guild.members:
            if member.name == "Orisa" or member.name == "Doom":
                continue
            globalMap[member.name] = datetime.datetime.now()
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
            outputstr += "In this session, {} unique instructions have been processed\n".format(numInstr + 1) # +1 for current instruction
            # Saving this space for any other meta information people might need
        await message.channel.send(outputstr)
        writeToFile(outputstr)
    
    if "!help" in message.content.lower() and "685642740788101141" in message.content.lower():
        outputstr = "Hello world! I am Orisa, a bot created by Zoid\n" 
        outputstr += "I was built to manage grouping up for esports teams!\n"
        outputstr += "Basic Commands\n"

        await message.channel.send(outputstr)

        t = PrettyTable(['Command', 'Function'])
        t.add_row(['\"!help @Orisa\"', 'invokes this message'])
        t.add_row(['\"!on\"', 'sets your status as online.'])
        t.add_row(['\"!off\"', 'sets your status as offline'])
        t.add_row(['\"!whoison\"', 'shows a list of everyone who is online mapped to their online time'])
        
        outputstr = str(t)
        await message.channel.send(outputstr)
        
        t = PrettyTable(['Command', 'Function'])
        t.add_row(['\"!status\"', 'ping the bot to test if everything is running smoothly'])
        t.add_row(['\"!status -v\"', '(VERBOSE) displays a list of meta statistics'])
        
        outputstr = str(t)
        await message.channel.send(outputstr)

        if "admin" in  [y.name.lower() for y in message.author.roles]:
            outputstr = "Since you are an admin, you also get access to the following commands\n"
            t = PrettyTable(['Command', 'Function'])
            t.add_row(['\"!on @<a user>\"', 'sets a user\'s status as online'])
            t.add_row(['\"!off @<a user>\"', 'sets a user\'s status as offline'])
            t.add_row(['\"!allon\"', 'sets every user\'s status as online'])
            t.add_row(['\"!alloff\"', 'sets every user\'s status as offline'])
        
            outputstr += str(t)
            await message.channel.send(outputstr)

        outputstr = "The code behind me is available on github at https://github.com/BhavdeepSinghB/Orisa\n"
        outputstr += "For any feature reccomendations, feel free to drop a message in the #suggestions channel, and mention Zoid\n"
        outputstr += "All the best, ya Rebel Scum!\n"
        

        await message.channel.send(outputstr)
        writeToFile("Help command invoked by {}".format(message.author.name))

    # Grouping
    if "!group" in message.content.lower():
        if message.author.name == "Orisa":
            return
        blockedList = []
        acceptedList = []
        callerGroup = None
        if '@' not in message.content.lower():
            await message.channel.send("Usage !group @<user> or [list of users]")
            writeToFile("{} used incorrect group creation syntax".format(message.author.name))
            return
        elif message.author.name not in [*globalMap]:
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
                if int(i) in [*allgrouped] or getUser(int(i), message) not in [*globalMap]:
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

    if "!ungroup" in message.content.lower():
        if message.author.name == "Orisa":
            return
        callerGroup = None
        if message.author.name not in [*globalMap]:
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
    
    #Practice Command for admins, to avoid spam
    if "!practice" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        # Making copies here to accomodate removal of maps that have already been played
        control = copy.copy(CONTROL)
        assault = copy.copy(ASSAULT)
        escorthyb = copy.copy(ESCORTHYB)

        uniqueCaps = True
        uniqueMaps = True
        customMaps = False

        if "-nuc" in message.content.lower():
            uniqueCaps = False
        if "-num" in message.content.lower():
            uniqueMaps = False
        if "-cm" in message.content.lower():
            customMaps = True
        # Take all online members at the time of invoking
        allOn = [*globalMap]
        
        numGames = int(message.content.lower().split(' ')[1])

        outputstr = "Creating a"
        
        if customMaps:
            outputstr += " custom"
            allmaps = (control + assault + escorthyb)
            random.shuffle(allmaps)
            for i in allmaps:
                i = i.lower()
            args = message.content.lower().split(' ')[2:]
            for i in args:
                if '-' in i:
                    args.remove(i)
            if len(args) == 0:
                await message.channel.send("Please provide at least one map to make a custom practice session")
                return
            for unformattedmap in args:
                for formattedmap in allmaps:
                    if unformattedmap.lower() in formattedmap.lower():
                        args.insert(args.index(unformattedmap), formattedmap)
                        args.remove(unformattedmap)

        outputstr += " practice session with {} players".format(len(allOn))
        if uniqueCaps:
            outputstr += " where captains will be unique"
        else:
            outputstr += " where captains MAY repeat"
        if not customMaps or (customMaps and len(args) < numGames):
            if uniqueMaps:
                outputstr += " and maps will be unique"
            else:
                outputstr += " and maps MAY repeat"
        await message.channel.send(outputstr)
        writeToFile(outputstr)

        if len(allOn) < 12:
            await message.channel.send("Seems like less than 12 players are online, if you have enough randos or those who aren't online, please react with 👍 to proceed WITHIN 60 SECONDS")

            def check(reaction, user):
                return user == message.author and str(reaction.emoji) == '👍'
            
            try:
                await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError as e:
                await message.channel.send("Time Out, please invoke practice again when you are ready")
                return

        if 2*numGames > len(allOn):
            await message.channel.send("Not enough unique captains for the number of games specified, captains will be repeated")
            uniqueCaps = False
        
        if numGames < 3:
            outputstr = "The number of games does not cover all game modes, you will start with Control map"
            if numGames == 2:
                outputstr += " and have a game of Assault/2CP"
            await message.channel.send(outputstr)
        
        

        i = 0
        while i < numGames:
            if customMaps:
                try:
                    gameMap = args[i]
                    if uniqueMaps:
                        if gameMap in assault:
                            assault.remove(gameMap)
                        elif gameMap in control:
                            control.remove(gameMap)
                        elif gameMap in escorthyb:
                            escorthyb.remove(gameMap)
                except IndexError as e:
                    customMaps = False
                    continue
            elif (i+1) % 3 == 0:
                gameMap = escorthyb[random.randint(0, len(escorthyb)-1)]
                if uniqueMaps: 
                    escorthyb.remove(gameMap)
            elif (i+1) % 2 == 0:
                gameMap = assault[random.randint(0, len(assault)-1)]
                if uniqueMaps:
                    assault.remove(gameMap)
            else:
                gameMap = control[random.randint(0, len(control)-1)]
                if uniqueMaps:
                    control.remove(gameMap)

            cap1 = allOn[random.randint(0, len(allOn)-1)]
            cap2 = allOn[random.randint(0, len(allOn)-1)]
            while(cap2 == cap1):
                cap2 = allOn[random.randint(0, len(allOn)-1)]
            if uniqueCaps:
                allOn.remove(cap1)
                allOn.remove(cap2)
            await message.channel.send("Game {}: {} vs {}\nMap: {}".format(i + 1, cap1, cap2, gameMap))
            i += 1

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

