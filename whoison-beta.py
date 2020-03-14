import discord
import datetime

TOKEN = 'Njg3Nzk4OTY4NjA4MDk2NTU0.XmrAwA.xNH4RxIghlme8ULsYaejH8oiUmo'
client = discord.Client()
filename = str(datetime.datetime.timestamp(datetime.datetime.now())) + ".log"
globalMap = {}
groupMap = {}


def writeToFile(outputstr):
    f = open(filename, "a")
    f.write("[{}]: {}\n".format(datetime.datetime.timestamp(datetime.datetime.now()), outputstr))
    f.close()


def getID(unformattedID):
    if str(unformattedID[0]) == '!':
        unformattedID = unformattedID.lstrip('!')
    for i in unformattedID:
        if i in ['>', '<', '!', ' ']:
            unformattedID = unformattedID.replace(i, '')
    return unformattedID


def getUser(id, message):
    for member in message.guild.members:
        if id == str(member.id):
            return member.name
    return "None"

def ungroup(message):
    outputstr = "Removed {} from group".format(message.author.name)
    for user in groupMap:
        if message.author.name == user:
            listOfStillGrouped = groupMap[user]
            del groupMap[user]
            if len(listOfStillGrouped) == 0:
                writeToFile(outputstr)
                return outputstr
            listOfStillGrouped.remove(listOfStillGrouped[0])
            groupMap[listOfStillGrouped[0]] = listOfStillGrouped
            outputstr += " New group leader is %s" % (listOfStillGrouped[0])
            writeToFile(outputstr)
            return outputstr
        for i in groupMap[user]:
            if message.author.name == i:
                groupMap[user].remove(i)
                if len(groupMap[user]) == 0:
                    del groupMap[user]
                writeToFile(outputstr)
                return outputstr
    outputstr = "Sorry, {}, you were not in a group".format(message.author.name)
    return outputstr


@client.event
async def on_message(message):
    if "!on" in message.content.lower():
        addedPerson = message.author.name
        if message.author.name == "WhoIsOn":
            return
        if "@" in message.content.lower():
            if "admin" in [y.name.lower() for y in message.author.roles]:
                addedPersonID = getID(message.content.split("@")[1])
                outputstr = "Admin command invoked by {}".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(outputstr)
                addedPerson = getUser(addedPersonID, message)
            else:
                outputstr = "Sorry, {}, you do not have admin privellages!, you cannot invoke off or on for other users".format(
                    message.author.name)
                await message.channel.send(outputstr)
                writeToFile(outputstr)
                return
        globalMap[addedPerson] = datetime.datetime.now()
        outputstr = "{} is now online!".format(addedPerson)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

    if message.content.lower().startswith("!whoison"):
        sortedList = sorted(globalMap.items(), key=lambda x: x[1])
        end = datetime.datetime.now()
        if len(sortedList) == 0:
            outputstr = "No one is on at the moment, {}, if you're going online, say \"!on\" to let people know!".format(
                message.author.name)
            await message.channel.send(outputstr)
            writeToFile(outputstr)
            return
        for i in sortedList:
            outputstr = "{} has been on for {}".format(i[0], str((end - i[1])))
            await message.channel.send(outputstr.split('.')[0])
            writeToFile(outputstr)

    if "!off" in message.content.lower():
        deletedPerson = message.author.name
        if message.author.name == "WhoIsOn":
            return
        if "@" in message.content.lower():
            if "admin" in [y.name.lower() for y in message.author.roles]:
                deletedPersonID = message.content.split("@")[1]
                deletedPersonID = getID(deletedPersonID)
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
        #If user was in any existing group, kick em out
        outputstr = ungroup(message)
        await message.channel.send(outputstr)

    # Admin commands
    if "!allon" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        for member in message.guild.members:
            if member.name == "WhoIsOn" or member.name == "Doom":
                continue
            globalMap[member.name] = datetime.datetime.now()
        outputstr = "Admin command invoked by {}, everyone is on!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

    if "!alloff" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        outputstr = "Admin command invoked by {}, everyone is off!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

    # Grouping
    if "!group" in message.content.lower():
        groupMap[message.author.name] = []
        listOfUsers = message.content.split('@')
        listOfUsers.remove(listOfUsers[0])
        listOfIDs = []
        for i in listOfUsers:
            something = getID(i)
            listOfIDs.append(something)
        listOfUsers = []
        ignoredUsers = []
        for i in listOfIDs:
            listOfUsers.append(getUser(i, message))
        for i in listOfUsers:
            if i == message.author.name or i == "WhoIsOn":
                listOfUsers.remove(i)
                ignoredUsers.append(i)
                continue
            if i not in globalMap:
                ignoredUsers.append(i)
                listOfUsers.remove(i)
                continue
            for j in groupMap.values():
                if i in j:
                    ignoredUsers.append(i)
                    listOfUsers.remove(i)
                continue
            listOfAlreadyGrouped = groupMap[message.author.name]
            listOfAlreadyGrouped.append(i)
            groupMap[message.author.name] = listOfAlreadyGrouped
        outputstr = "Adding the following users to {}'s group ".format(message.author.name)
        # await message.channel.send(outputstr)
        for i in listOfUsers:
            outputstr = outputstr + i + ' '
        await message.channel.send(outputstr)
        writeToFile(outputstr)
        if len(ignoredUsers) != 0:
            outputstr = "The following users are ignored from the group, since they are not online, are in someone's group or are yourself or a bot "
            for i in ignoredUsers:
                outputstr = outputstr + i + ' '
            outputstr += "\nIf you are on, please invoke the  \"!on\" command (or admin command) and group again"
            await message.channel.send(outputstr)
            writeToFile(outputstr)

    # This is not an admin command
    if "!ungroup" in message.content.lower():
        outputstr = ungroup(message)
        await message.channel.send(outputstr)

    if "!whoisgrouped" in message.content.lower():
        outputstr = "The following groups currently exist"
        for user in groupMap:
            outputstr += "\n{}'s group: ".format(user)
            for i in groupMap[user]:
                outputstr = outputstr + i + ' '
        await message.channel.send(outputstr)
        writeToFile(outputstr)
        return


@client.event
async def on_ready():
    print("Hello world!")
    channel = client.get_channel(685725528023760926)
    await channel.send("Who is on bot is now live in beta! Welcome beta users! Feel free to try to break me!")


client.run(TOKEN)