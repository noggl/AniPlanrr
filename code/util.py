# If in docker container
import time
import os
from dotenv import load_dotenv
import re


if os.path.exists('config/.env'):
    # Assume repo structure
    configPath = 'config/'
else:
    # set config path string to /config
    configPath = '/config/'

load_dotenv('config/.env')
SONARRURL = os.getenv('SONARRURL')
SONARRAPIKEY = os.getenv('SONARRAPIKEY')
ANILIST_USERNAME = os.getenv('ANILIST_USERNAME')
MONITOR = os.getenv('MONITOR')
RETRY = os.getenv('RETRY')
AUTO_FILL_MAPPING = os.getenv('AUTO_FILL_MAPPING')
LOGGING = os.getenv('LOGGING')
RADARRURL = os.getenv('RADARRURL')
RADARRAPIKEY = os.getenv('RADARRAPIKEY')

logPath = configPath+'log/'


def pr(string):
    print(string)
    if LOGGING is not None:
        with open(logPath + 'log.txt', 'a') as f:
            # if file is not empty, add newline
            if os.stat(logPath + 'log.txt').st_size != 0:
                f.write('\n')
            # write timestamp + string
            f.write(time.strftime("%Y-%m-%d %H:%M:%S",
                    time.localtime()) + ': ' + string)


def loadIgnoreList():
    # if ignore.csv doesn't exist, create it
    if not os.path.exists(configPath + 'ignore.csv'):
        pr("ignore.csv doesn't exist, creating it")
        with open(configPath + 'ignore.csv', 'w') as f:
            f.write('')
    ignoreList = []
    with open(configPath + 'ignore.csv', 'r') as f:
        for line in f:
            # check that file can be split into 2 parts
            if len(line.strip().split(';')) != 2:
                pr("Error: ignore.csv is not formatted correctly")
            else:
                arr = line.strip().split(';')
                # check that id is an int
                if not arr[1].isdigit():
                    pr("Error: ignore.csv is not formatted correctly")
                else:
                    ignoreList.append(int(arr[1]))
    return ignoreList


def loadMappingList():
    # if mapping.csv doesn't exist, create it
    if not os.path.exists(configPath + 'mapping.csv'):
        pr("mapping.csv doesn't exist, creating it")
        with open(configPath + 'mapping.csv', 'w') as f:
            f.write('')
    mapping = []
    with open(configPath + 'mapping.csv', 'r') as f:
        for line in f:
            # check that file can be split into 4 parts
            if len(line.strip().split(';')) != 4:
                pr("Error: mapping.csv is not formatted correctly")
            else:
                arr = line.strip().split(';')
                # check that 2nd, third and fourth part are ints
                if not arr[1].isdigit() or not arr[2].isdigit() or not arr[3].isdigit():
                    pr("Error: mapping.csv is not formatted correctly")
                else:
                    mapping.append(
                        [arr[0], int(arr[1]), int(arr[2]), int(arr[3])])
    return mapping


def addToIgnoreList(title, id):
    ignoreList = loadIgnoreList()
    # if id isn't already in ignorelist
    if id not in ignoreList:
        # add id to ignorelist
        pr("Adding " + title + " to ignore list")
        with open(configPath + 'ignore.csv', 'a') as f:
            # if file is not empty, add newline
            if os.stat(configPath + 'ignore.csv').st_size != 0:
                f.write('\n')
            f.write(title + ';' + str(id))
    else:
        pr(title + " is already in ignore list")


def cleanText(string):
    return re.sub(r'[^\w\s]', '', str(string)).lower()


def getListDifference(list1, list2):
    # ignore third element of every object
    list1_strip = [i[:2] for i in list1]
    list2_strip = [i[:2] for i in list2]
    # Get index of every object in list1 that is not in list2
    diff = []
    for i in list1_strip:
        if i not in list2_strip:
            diff.append(list1_strip.index(i))

    # return list of objects in list1 that are not in list2
    return [list1[i] for i in diff]


def dumpVar(name, var):
    with open(logPath + name + '-dump.txt', 'a') as f:
        # if file is not empty, add newline
        pr("Dumping " + name + " to " + name + "-dump.txt")
        if os.stat(logPath + name + '-dump.txt').st_size != 0:
            f.write('\n\n')
        # write timestamp + string
        f.write(time.strftime("%Y-%m-%d %H:%M:%S",
                time.localtime()) + '\n' + str(var))


def addMapping(title, anidb_id, tmdb_id, season):
    mapping = loadMappingList()
    # if mapping doesn't already exist
    if [title, anidb_id, tmdb_id, season] not in mapping:
        # add mapping to mapping.csv
        pr("Adding mapping: " + title + " " + str(anidb_id) +
           " " + str(tmdb_id) + " " + str(season))
        # if not the first line in mapping.csv, add a new line
        if os.stat(configPath + 'mapping.csv').st_size != 0:
            with open(configPath + 'mapping.csv', 'a') as f:
                f.write("\r")
        with open(configPath + 'mapping.csv', 'a') as f:
            f.write(str(title) + ";" + str(anidb_id) +
                    ";" + str(tmdb_id) + ";" + str(season))
    else:
        pr("Mapping already exists: " + title + " " + str(anidb_id) +
           " " + str(tmdb_id) + " " + str(season))
