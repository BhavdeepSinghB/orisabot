import signal
import datetime
import json
import os.path

"""
Project Name: Hermes

- Handler for SIGKILL and SIGINT 
- Writes current state to json file
- Gracefully shuts down
- TODO : Load current state from json file into Orisa object

"""

class Hermes:
    __core = None
    __enabled = False
    __interval = 0
    __filename = None
    __logfilename = None
    signals = [signal.SIGINT, signal.SIGTERM]

    def __init__(self, settings, logfilename):
        self.__enabled = settings.get('enabled', False)
        self.__interval = settings.get('interval', 0)
        self.__filename = f"backups/coredump.bak" #TODO add a backup task in the future
        self.__logfilename = logfilename
        self.__config = {}
    
    @property
    def config(self):
        return self.__config

    @property
    def enabled(self):
        return self.__enabled
    
    @property
    def interval(self):
        return self.__interval

    def log(self, outputstr):
        writeToFile(self.__logfilename, outputstr)

    def attach_core(self, Core):
        self.__core = Core

    def _format_globalMap(self, globalMap):
        id_globalMap = {}
        for i in globalMap.keys():
            try: 
                id_globalMap[i.id] = globalMap[i].isoformat()
            except KeyError:
                # Log this 
                id_globalMap[i.id] = None
        return id_globalMap 
    
    def _format_notify_dict(self, notifyDict):
        id_notifyDict = {}
        for i in notifyDict.keys():
            try:
                id_notifyDict[i.id] = [u.id for u in notifyDict[i]]
            except AttributeError:
                id_notifyDict["All"] = [u.id for u in notifyDict["All"]]
            except KeyError:
                # Log this failure
                id_notifyDict[i] = None
        return id_notifyDict

    def write_config(self):
        globalMap = self.__core.get_online_users()
        self.__config['globalMap'] = self._format_globalMap(globalMap) 
        notifyDict = self.__core.notif_data
        self.__config['notifyDict'] = self._format_notify_dict(notifyDict)
        smurfList = self.__core.smurfs
        self.__config['smurfList'] = [x.id for x in smurfList]
        with open(self.__filename, 'w') as outfile:
            json.dump(self.__config, outfile, indent=2)
        
    def read_config(self):
        if os.path.isfile(self.__filename):
            with open(self.__filename) as backup_file:
                self.__config = json.load(backup_file)
                return True
        # Log this
        print("Could not find file")
        return False



