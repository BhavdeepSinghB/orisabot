import gspread, asyncio, copy, os
from oauth2client.service_account import ServiceAccountCredentials
from modules.utils import writeToFile

class SpreadService:
    # Variables
    __sheet = None
    __filename = None
    __index_dict = {}
    __lastID = -1
    
    @classmethod
    async def construct(cls, filename):
        self = SpreadService()
        
        self.__filename = filename

        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('modules/client_secret.json', scope)
        client = gspread.authorize(creds)
         
        self.__sheet = client.open("Overwatch Team SR").sheet1

        for i in self.__sheet.get_all_records():
            try:
                self.__index_dict[i['Name']] = int(i['ID']) + 1 
            except ValueError:
                continue
        self.__lastID = sorted(self.__index_dict.keys())[-1]
        outputstr = "Successfully constructed SpreadService"
        print(outputstr)
        writeToFile(self.__filename, outputstr)

        return self

    async def sr(self, message):
        sheet = self.__sheet
        if "-team" in message.content.lower():
            records = sheet.get_all_records()
            averageDict = records[-1] #average is the last row in the sheet
            outputstr = "Team Averages for {}\n".format(message.guild.name)
            try:
                outputstr += "Average Team SR (based on highest role) : {:.2f}\n".format(averageDict['Highest SR'])
                outputstr += "Tank average : {:.2f}\n".format(averageDict['Tank'])
                outputstr += "DPS average : {:.2f}\n".format(averageDict['DPS'])
                outputstr += "Support average : {:.2f}\n".format(averageDict['Support'])
                await message.channel.send(outputstr)
                writeToFile(self.__filename, outputstr)
            except KeyError as e:
                writeToFile("Error reporting SR: {}".format(e))
            return    

        index_dict = self.__index_dict
        mentionList = message.mentions
        if mentionList is None or len(mentionList) == 0:
            mentionList.append(message.author)
        for i in mentionList:
            try:
                outputstr = "SR for {} for Season {}\n".format(i.nick if i.nick is not None else i.name, sheet.acell('B{}'.format(index_dict[i.name])).value)
                outputstr += "Tank : {}\n".format(sheet.acell('C{}'.format(index_dict[i.name])).value)
                outputstr += "Damage : {}\n".format(sheet.acell('D{}'.format(index_dict[i.name])).value)
                outputstr += "Support : {}\n".format(sheet.acell('E{}'.format(index_dict[i.name])).value)
                await message.channel.send(outputstr)
                writeToFile(self.__filename, outputstr)
            except KeyError as e:
                outputstr = "Whoops! Seems like I can't find any data for {}. Are you sure you're registered? Use !register to add yourself to the database".format(i.name)
                await message.channel.send(outputstr)
                outputstr = "Error reporting SR : {}".format(e)
                writeToFile(self.__filename, outputstr)
    
    async def set(self, message):
        sheet = self.__sheet
        
        mentions = message.mentions
        if len(mentions) > 0:
            if "admin" in [y.name.lower() for y in message.author.roles]:
                user = mentions[0]
            else:
                outputstr = "Sorry, {}. You'll need admin permissions to do that".format(message.author.name)
                await message.channel.send(outputstr)
                writeToFile(self.__filename, outputstr)
                return
        else:
            user = message.author
        
        args = message.content.split(' ')
        
        try:
            role = args[-2]
        except IndexError as e:
            outputstr = "Usage: !set {@user} role <sr>"
            writeToFile(self.__filename, "{}: ".format(message.author.name) + outputstr)
            outputstr += "\nList of acceptable roles - ['tank', 'dps', 'damage', 'dmg', 'support', 'heals']"
            await message.channel.send(outputstr)
            return

        roleList = ['tank', 'dps', 'damage', 'dmg', 'support', 'heals']
        
        if not role in roleList:
            outputstr = "Usage: !set {@user} role <sr>"
            writeToFile(self.__filename, "{}: ".format(message.author.name) + outputstr)
            outputstr += "\nList of acceptable roles - ['tank', 'dps', 'damage', 'dmg', 'support', 'heals']"
            await message.channel.send(outputstr)
            return
        
        try:
            newSR = int(args[-1])
        except ValueError:
            outputstr = "Please make sure the SR is correctly written as the last part of the message"
            writeToFile(self.__filename, "Invoked by {}: ".format(message.author.name) + outputstr)
            await message.channel.send(outputstr)
            return
        
        if newSR < 0:
            outputstr = "{}, please make sure the SR is a positive number".format(message.author.name)
            writeToFile(self.__filename, outputstr)
            await message.channel.send(outputstr)
            return
        
        if user.name not in self.__index_dict.keys():
            outputstr = "Whoops I can't find any details for {}. If you're not registered, type !register to start!".format(user.name)
            writeToFile(self.__filename, outputstr)
            await message.channel.send(outputstr)
            return

        # At this point, user and SR should be verified. Figure out the cell
        if role == 'tank':
            cell = "C"
        elif role in ('dps', 'damage', 'dmg'):
            cell = "D"
        else:
            cell = "E"

        try:
            cell += str(self.__index_dict[user.name])
        except KeyError as e:
            await message.channel.send("This is embarassing. I'm not sure what went wrong, but something did. Please try later")
            writeToFile(self.__filename, "Error in user validation {}".format(e))
            return
        
        sheet.update(cell, newSR)
        outputstr = "Successfully changed {}'s {} SR to {}".format(user.name, role, newSR)
        await message.channel.send(outputstr)
        writeToFile(self.__filename, outputstr)

