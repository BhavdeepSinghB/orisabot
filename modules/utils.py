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