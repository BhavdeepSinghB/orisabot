import discord
import datetime
from prettytable import PrettyTable

TOKEN = '' #Your token here 
client = discord.Client()
filename = str(datetime.datetime.timestamp(datetime.datetime.now())) + ".log"
globalMap = {}
START = datetime.datetime.now()
numInstr = 0

def writeToFile(outputstr):
    global numInstr
    f = open(filename, "a")
    f.write("[{}]: {}\n".format(datetime.datetime.timestamp(datetime.datetime.now()), outputstr))
    f.close()
    numInstr += 1


@client.event
async def on_message(message):
    global numInstr
    if "!on" in message.content.lower():
        addedPerson = message.author.name
        if message.author.name == "WhoIsOn":
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


    if message.content.lower().startswith("!whoison"):
        if message.author.name == "WhoIsOn":
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
        if message.author.name == "WhoIsOn":
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
                for member in message.guild.members:
                    if deletedPersonID == str(member.id):
                        deletedPerson = member.name
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

    #Admin commands
    if "!allon" in message.content.lower() and "admin" in [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        for member in message.guild.members:
            if member.name == "WhoIsOn" or member.name == "Doom":
                continue
            globalMap[member.name] = datetime.datetime.now()
        outputstr = "Admin command invoked by {}, everyone is on!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

    if "!alloff" in message.content.lower() and "admin" in  [y.name.lower() for y in message.author.roles]:
        globalMap.clear()
        outputstr = "Admin command invoked by {}, everyone is off!".format(message.author.name)
        await message.channel.send(outputstr)
        writeToFile(outputstr)

    # Status Commands
    if "!status" in message.content.lower():
        if message.author.name == "WhoIsOn":
            return
        duration = datetime.datetime.now() - START
        outputstr = "The bot is online and has been running for {}\n".format(str(duration).split('.')[0])
        if "-v" in message.content.lower():
            outputstr += "In this session, {} unique instructions have been processed\n".format(numInstr + 1) # +1 for current instruction
            # Saving this space for any other meta information people might need
        await message.channel.send(outputstr)
        writeToFile(outputstr)
    
    if "!help" in message.content.lower() and "685642740788101141" in message.content.lower():
        outputstr = "Hello world! I am WhoIsOn, a bot created by Zoid\n" 
        outputstr += "I was built to manage grouping up for esports teams!\n"
        outputstr += "Basic Commands\n"

        await message.channel.send(outputstr)

        t = PrettyTable(['Command', 'Function'])
        t.add_row(['\"!help @WhoIsOn\"', 'invokes this message'])
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

        outputstr = "The code behind me is available on github at https://github.com/BhavdeepSinghB/whoison\n"
        outputstr += "For any feature reccomendations, feel free to drop a message in the #suggestions channel, and mention Zoid\n"
        outputstr += "All the best, ya Rebel Scum!\n"
        

        await message.channel.send(outputstr)
        writeToFile("Help command invoked by {}".format(message.author.name))


@client.event
async def on_ready():
    print("Ready")
    writeToFile("Ready")


client.run(TOKEN)

