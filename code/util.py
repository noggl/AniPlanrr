import time
import os
from dotenv import load_dotenv
import re
from copy import copy
import json
import sqlite3
import csv

# If in docker container
if os.path.exists('config/.env'):
    # Assume repo structure
    configPath = 'config/'
else:
    # set config path string to /config
    configPath = '/config/'

load_dotenv('config/.env')
SONARRURL = os.getenv('SONARRURL')
SONARRAPIKEY = os.getenv('SONARRAPIKEY')
SONARRANIMEPATH = os.getenv('SONARRANIMEPATH')
ANILIST_USERNAME = os.getenv('ANILIST_USERNAME')
MONITOR = os.getenv('MONITOR')
RETRY = os.getenv('RETRY')
RESPECTFUL_ADDING = os.getenv('RESPECTFUL_ADDING')
AUTO_FILL_MAPPING = os.getenv('AUTO_FILL_MAPPING')
LOGGING = os.getenv('LOGGING')
RADARRURL = os.getenv('RADARRURL')
RADARRAPIKEY = os.getenv('RADARRAPIKEY')
RADARRANIMEPATH = os.getenv('RADARRANIMEPATH')

logPath = configPath + 'log/'
mappingFile = configPath + 'mapping.csv'


def pr(string):
    print(string)
    if LOGGING is not None:
        # create log folder
        if not os.path.exists(logPath):
            os.makedirs(logPath)
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
    if not os.path.exists(mappingFile):
        pr("mapping.csv doesn't exist, creating it")
        with open(mappingFile, 'w') as f:
            f.write('')
    mapping = []
    with open(mappingFile, 'r') as f:
        reader =csv.reader(f, delimiter=';')
        for row in reader:
            arr = row
            # check that file can be split into 4 parts
            if len(arr) != 4:
                pr("Error: mapping.csv is not formatted correctly")
            else:
                # check that id is an int
                if not arr[1].isdigit() or not arr[2].isdigit() or not arr[3].isdigit():
                    pr("Error: mapping.csv is not formatted correctly")
                else:
                    mapping.append({'title': arr[0], 'anilistId': int(
                        arr[1]), 'tmdb_or_tvdb_Id': int(arr[2]), 'season': int(arr[3])})
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
    return re.sub(r'[^\w\s]', '', str(string)).lower().rstrip("'`~")

def stripExtraKeys(item):
    entry = copy(item)
    # removes anilistId and season from show/movie
    if 'anilistId' in entry:
        entry.pop('anilistId', None)
    if 'season' in entry:
        entry.pop('season', None)
    return entry

def dumpVar(name, var):
    # create log folder
    if not os.path.exists(logPath):
        os.makedirs(logPath)
    # if file doesnt exist, create it
    if not os.path.exists(logPath + name + '-dump.txt'):
        with open(logPath + name + '-dump.txt', 'w') as f:
            f.write('')
    with open(logPath + name + '-dump.txt', 'a') as f:
        # if file is not empty, add newline
        pr("Dumping " + name + " to " + name + "-dump.txt")
        if os.stat(logPath + name + '-dump.txt').st_size != 0:
            f.write('\n\n')
        # write timestamp + string
        f.write(time.strftime("%Y-%m-%d %H:%M:%S",
                time.localtime()) + '\n' + str(var))


def addMapping(item):
    if LOGGING:
        pr("Trying to map this item...")
    mapping = loadMappingList()
    # if mapping['anilistId] isn't already in mapping list
    if item['anilistId'] not in [i['anilistId'] for i in mapping]:
        # if tmdb_or_tvdb_Id exists, set newID to it, otherwise, set tmdbId to it
        if 'tmdb_or_tvdb_Id' in item:
            newId = item['tmdb_or_tvdb_Id']
        if 'tmdbId' in item:
            newId = item['tmdbId']
        if 'tvdbId' in item:
            newId = item['tvdbId']
        if 'tmdb_or_tvdb_Id' not in item and 'tmdbId' not in item and 'tvdbId' not in item:
            pr("Error: " + item['title'] + " has no tmdbId or tvdbId")
            return False
    if 'season' not in item:
        item['season'] = 1
        # add mapping to mapping.csv
        pr("Adding mapping: " + item['title'] + " " + str(item['anilistId']) +
            " " + str(newId) + " " + str(item['season']))
        # if not the first line in mapping.csv, add a new line
        if os.stat(mappingFile).st_size != 0:
            with open(mappingFile, 'a') as f:
                f.write("\r")
        with open(mappingFile, 'a') as f:
            f.write(item['title'] + ";" + str(item['anilistId']) +
                    ";" + str(newId) + ";" + str(item['season']))
            return True


def animeMatch(result, show):
    matching = 0
    # Check romanji and english title VS all titles in results
    #if result['title'] contains year in paranthesis, remove the year
    if re.search(r'\(\d{4}\)', result['title']):
        result['title'] = re.sub(r'\(\d{4}\)', '', result['title']).rstrip()
    for title in show['titles'].values():
        if title is None:
            continue
        if cleanText(title) == cleanText(result['title']):
            if LOGGING:
                pr("Matched in title: " + title + " & " + result['title'])
            matching += 1
            break
        else:
            if LOGGING:
                pr("DID NOT match in title: " + title + " & " + result['title'])
    if show['year'] == result['year']:
        if LOGGING:
            pr("Matched in year: " + str(show['year']))
        matching += 1
    else:
        if LOGGING:
            pr("DID NOT matched in year: " + str(show['year']) + " & " + str(result['year']))
    # List of all keys we've investigated already
    investigated = ['year', 'title']
    for key in show:
        if key not in investigated:
            if key in result:
                if isinstance(result[key], str) and isinstance(show[key], str):
                    first = cleanText(result[key])
                    second = cleanText(show[key])
                else:
                    first = result[key]
                    second = show[key]

                if first == second:
                    matching += 1
    if matching >= 2:
        if LOGGING:
            pr("Matched on two or more! It is: " + str(result['tvdbId']))
        return result['tvdbId']
    else:
        if LOGGING:
            pr("Failed to match...")
        return False


def compareDicts(dict1, dict2):
    # find which dict is smaller
    if len(dict1) < len(dict2):
        small = dict1
        big = dict2
    else:
        small = dict2
        big = dict1
    for key in small:
        if key in big:
            # if values are strings
            if isinstance(small[key], str) and isinstance(big[key], str):
                if cleanText(small[key]) != cleanText(big[key]):
                    return False
            else:
                if small[key] != big[key]:
                    return False
    return True


def diffDicts(dict1, dict2):
    # It might be better to not have the int and error parts and just keep the cleanText for string, passing the other checks through normally
    diff = []
    for i in dict1:
        # if there is no matching object in dict2, append it to diff
        if not any(compareDicts(i, j) for j in dict2):
            diff.append(i)
    return diff
