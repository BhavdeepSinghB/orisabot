import random
import asyncio

async def practice(message, globalMap, client): 
    # Making copies here to accomodate removal of maps that have already been played
    CONTROL = ['Busan', 'Ilios', 'Lijang Tower', 'Nepal', 'Oasis']
    ASSAULT = ['Hanamura', 'Temple of Anubis', 'Volskaya Industries']
    ESCORTHYB = ['Dorado', 'Havana', 'Junkertown', 'Rialto', 'Route 66', 'Watchpoint Gibraltar', 'Blizzard World', 'Eichenwalde', 'Hollywood', 'King\'s Row', 'Numbani']

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
    #print(globalMap)
    # return
    allOn = list(globalMap.keys())

    try:
        numGames = int(message.content.lower().split(' ')[1])
    except IndexError:
        await message.channel.send("Syntax: !practice [-flags] <number of games>")
        return
    
    if len(allOn) < 2:
        await message.channel.send("Can't create a practice session with less than 2 online players")
        return

    outputstr = "Creating a"

    if customMaps:
        outputstr += " custom"
        allmaps = (CONTROL + ASSAULT + ESCORTHYB)
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
    # writeToFile(outputstr)

    if len(allOn) < 12:
        await message.channel.send("Seems like less than 12 players are online, if you have enough randos or those who aren't online, please react with 👍 to proceed WITHIN 60 SECONDS")

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) == '👍'
        
        try:
            await client.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Time Out, please invoke practice again when you are ready")
            return

    if 2*numGames > len(allOn):
        await message.channel.send("Not enough unique captains for the number of games specified, captains will be repeated")
        uniqueCaps = False

    if numGames < 3 and not customMaps:
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
                    if gameMap in ASSAULT:
                        ASSAULT.remove(gameMap)
                    elif gameMap in CONTROL:
                        CONTROL.remove(gameMap)
                    elif gameMap in ESCORTHYB:
                        ESCORTHYB.remove(gameMap)
            except IndexError:
                customMaps = False
                continue
        elif (i+1) % 3 == 0:
            gameMap = ESCORTHYB[random.randint(0, len(ESCORTHYB)-1)]
            if uniqueMaps: 
                ESCORTHYB.remove(gameMap)
        elif (i+1) % 2 == 0:
            gameMap = ASSAULT[random.randint(0, len(ASSAULT)-1)]
            if uniqueMaps:
                ASSAULT.remove(gameMap)
        else:
            gameMap = CONTROL[random.randint(0, len(CONTROL)-1)]
            if uniqueMaps:
                CONTROL.remove(gameMap)

        cap1 = allOn[random.randint(0, len(allOn)-1)]
        cap2 = allOn[random.randint(0, len(allOn)-1)]
        while(cap2 == cap1):
            cap2 = allOn[random.randint(0, len(allOn)-1)]
        if uniqueCaps:
            allOn.remove(cap1)
            allOn.remove(cap2)
        await message.channel.send("Game {}: {} vs {}\nMap: {}".format(i + 1, cap1.name, cap2.name, gameMap))
        i += 1