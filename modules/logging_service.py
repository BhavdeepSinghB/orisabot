import datetime
import asyncio
from discord import DiscordException


class LoggingService:
    def __init__(self, filename, log_channel=None):
        self.__filename = f"logs/{filename}.log"
        self.__log_channel = log_channel
        self.__sender = "---"

    @property
    def sender(self):
        return self.__sender
    
    @sender.setter
    def sender(self, sender):
        self.__sender = sender

    @property
    def log_channel(self):
        return self.__log_channel

    @log_channel.setter
    def log_channel(self, channel):
        self.__log_channel = channel

    def info(self, outputstr):
        self._log(outputstr)
    
    def error(self, outputstr):
        self._log(outputstr, type="ERR")
    
    def warn(self, outputstr):
        self._log(outputstr, type="WARN")
    
    def debug(self, outputstr):
        self._log(outputstr, type="DEBUG")
    
    def priv(self, outputstr, type="INFO", channel=None):
        if channel == None:
            if self.__log_channel:
                channel = self.__log_channel  
            else:
                raise AttributeError("No channel found")
        return self._log(outputstr, privilaged=True, type=type, channel=channel)

    def _log(self, outputstr, privilaged=False, type="INFO", channel=None):
        outputstr =  f"{datetime.datetime.now()} - [{self.__sender}] [{type}] " + outputstr
        # Write to file
        with open(self.__filename, "a") as logfile:
            logfile.write(outputstr)
            logfile.write("\n")
        # Send message to log channel
        if privilaged and channel:
            return asyncio.create_task(self._send_log_message(channel, outputstr))

    async def _send_log_message(self, channel, outputstr):
        try:
            await channel.send(outputstr)
        except DiscordException as e:
            print(e)
    