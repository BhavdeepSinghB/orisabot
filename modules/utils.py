import datetime 

def writeToFile(filename, outputstr):
    f = open(filename, "a")
    f.write("[{}]: {}\n".format(datetime.datetime.now(), outputstr))
    f.close()