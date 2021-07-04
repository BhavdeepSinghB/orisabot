from datetime import datetime
from modules.logging_service import LoggingService
from os import write
import copy

class Reaper:
    __paged_list = []
    __ack_list = []
    __config = {}
    __is_enabled = False
    __timeout = 60 # seconds
    __warn = False
    __warn_time = 30 # seconds
    __sleep_time = 10 # seconds
    __filename = None

    def __init__(self, config, log=None):
        if not config:
            self.__is_enabled = False
            return
        self.__is_enabled = config['enabled']
        self.__timeout = config['timeout']
        self.__warn = config['warn']
        if self.__warn:
            self.__warn_time = config['warn_time']
        self.__sleep_time = config['sleep_time']
        if log:
            self.log = copy.copy(log)
            self.log.sender = "REAPER"
        else:
            self.log = LoggingService

    @property
    def is_enabled(self):
        return self.__is_enabled
    
    @property
    def timeout(self):
        return self.__timeout
    
    def setup(self):
        """
        Returns:
        sleep_time in seconds as int if enabled 
        0 if disabled 
        """
        if self.__is_enabled:
            self.log.info(f'[SLEEP] {self.__sleep_time} seconds')
            return self.__sleep_time
        else:
            return 0
    
    def reap(self, user, online_time):
        """
        Returns:
        1 to issue reaping
        2 to issue page
        0 if neither
        """
        if not self.__is_enabled:
            return 0
        if  (datetime.now() - online_time).seconds > self.__timeout:
            if user in self.__paged_list: 
                self.__paged_list.remove(user) 
            if user in self.__ack_list: 
                self.__ack_list.remove(user) 
            self.log.info(f'Reaping issued for {user.name}')
            return 1 
        elif self.__warn and (datetime.now() - online_time).seconds > self.__warn_time: 
            if user not in self.__ack_list:
                self.__paged_list.append(user)
                self.log.info(f'Page issued for {user.name}')
                return 2
        return 0
        
    def ack(self, user):
        if not self.__is_enabled:
            return
        if user in self.__paged_list:
            self.__ack_list.append(user)
            return True
        return False


