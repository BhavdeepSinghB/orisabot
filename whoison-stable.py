import discord
import datetime

TOKEN = 'Njg1NjQyNzQwNzg4MTAxMTQx.XmLvYQ.IC8RS2kwc4FoMgbAYkUVi_qdPBc'
client = discord.Client()
filename = str(datetime.datetime.timestamp(datetime.datetime.now())) + ".log"
globalMap = {}

def writeToFile(outputstr):
    f = open(filename, "a")
    f.write("[{}]: {}\n".format(datetime.datetime.timestamp(datetime.datetime.now()), outputstr))
    f.close()

@client.event
async def on_message(message):
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



@client.event
async def on_ready():
    print("Hello world!")
    channel = client.get_channel(685725528023760926)
    await channel.send("Who is on bot is now live")


client.run(TOKEN)

