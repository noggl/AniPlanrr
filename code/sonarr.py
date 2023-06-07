
import requests
from util import *


def getSonarrList(SONARRURL, SONARRAPIKEY):
    response = requests.get(
        SONARRURL + "series?apikey=" + SONARRAPIKEY)
    # create list from response title and id
    if response.status_code != 200:
        pr("Error: Sonarr response is" + str(response.status_code) + ", not 200")
        if LOGGING:
            # write response to file
            dumpVar('failedSonarrResponse', response.json())
        return
    seriesList = []
    if LOGGING:
        # write response to file
        dumpVar('getSonarrResponse', response.json())
    # for each object in response
    for i in response.json():
        # if seriesType=anime
        if i['seriesType'] == "anime":
            seriesList.append(i)
    return seriesList

def setSeasons(show):
    # Not sure if this is how I want to do this. If I don't have the season==1,
    # and there is an explicit season 1, it will not follow MONITOR nor track season 2
    if 'season' not in show or show['season'] == 1:
        pr('season not set, setting to ' + str(MONITOR))
        show['addOptions'] = {'monitor': MONITOR,
                              "searchForMissingEpisodes": True}
        return show
    else:
        pr('season set, only setting specifically requested season')
        for i in range(len(show['seasons'])):
            if int(show['seasons'][i]['seasonNumber']) == show['season']:
                show['seasons'][i]['monitored'] = True
            else:
                # if this is a new show, set all other seasons to false
                if 'path' not in show:
                    show['seasons'][i]['monitored'] = False
        show['addOptions'] = {"searchForMissingEpisodes": 'true'}
        return show


def addShow(show):
    pr("Adding " + show['title'] + " to Sonarr")
    show = setSeasons(show)
    if getSonarrTagId("fromanilist") not in show['tags']:
        show['tags'].append(getSonarrTagId("fromanilist"))
    show['profileId'] = 1
    #set type to anime
    show['seriesType'] = 'anime'
    show['path'] = '/tv/Anime/' + show['title']
    # write show to file
    if LOGGING:
        dumpVar('addShowShow', show)
    response = requests.post(
        SONARRURL + 'series?apikey=' + SONARRAPIKEY, json=stripExtraKeys(show))
    # If resposne is 201, print success
    if response.status_code == 201:
        pr(show['title'] + " was added to Sonarr")
        dumpVar('addShowResponse', response.json())
        if AUTO_FILL_MAPPING:
            addMapping(show)
    else:
        pr("ERRROR: " + show['title'] + " could not be added to Sonarr")
        # write response to file
        if LOGGING:
            dumpVar('addShowResponse', response.json())


def search(string):
    search_string = string.replace(' ', '%20')
    search_string = search_string.replace(':', '%3A')
    response = requests.get(
        SONARRURL + 'series/lookup?apikey=' + SONARRAPIKEY + '&term=' + search_string)
    if LOGGING:
        dumpVar('searchResponse', response.json())
    return response.json()[0]


def updateSonarrSeason(show):
    pr("Adding " + show['title'] + " season " +
       str(show['season']) + " to Sonarr")
    # change "monitored" in entry['seasons'] to true where seasonNumber = season
    show = setSeasons(show)
    if getSonarrTagId("fromanilist") not in show['tags']:
        show['tags'].append(getSonarrTagId("fromanilist"))
    show['monitored'] = 'true'
    show['addOptions'] = {'monitor': MONITOR,
                          "searchForMissingEpisodes": 'true'}
    response = requests.put(
        SONARRURL + 'series/' + str(show['id']) + '?apikey=' + SONARRAPIKEY, json=stripExtraKeys(show))
    # If resposne is 201, print success
    if response.status_code == 202:
        pr(show['title'] + " season " +
           str(show['season']) + " was added to Sonarr")
        if AUTO_FILL_MAPPING:
            # write title, anilistId, tvdbID to mappings.csv
            addMapping(show)
    else:
        pr("ERRROR: " + show['title'] + " season " +
           str(show['season']) + " could not be added to Sonarr")
        # write response to file
        if LOGGING:
            dumpVar('updateSeasonResponse', response.json())


def getSonarrTagId(tag_name):
    params = {
        'label': tag_name
    }
    response = requests.get(SONARRURL + 'tag?apikey=' + SONARRAPIKEY)
    # get id of tag labeled "fronAniList"
    tag_id = None
    for i in response.json():
        if i['label'] == tag_name.lower():
            tag_id = i['id']
    # if tag_id was not found, create it
    if tag_id is None:
        response = requests.post(
            SONARRURL + 'tag?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))
        if response.status_code == 201:
            tag_id = response.json()['id']
    return tag_id


def sendToSonarr(newShows, mapping, sonarrList):
    listToAdd = []
    for show in newShows:
        if LOGGING:
            pr("Looking for ID for " + show['title'])
        if show['anilistId'] in [i['anilistId'] for i in mapping]:
            map = mapping[[i['anilistId']
                           for i in mapping].index(show['anilistId'])]
            pr(show['title'] + " is mapped to " +
               str(map['title']) + " season " + str(map['season']))
            # First check if show is in sonarrList (and therefore already in sonarr)
            if map['tmdb_or_tvdb_Id'] in [i['tvdbId'] for i in sonarrList]:
                # mapped show was already in sonarr
                result = sonarrList[[i['tvdbId']
                                     for i in sonarrList].index(map['tmdb_or_tvdb_Id'])]
                result['anilistId'] = map['anilistId']
                result['season'] = map['season']
            else:
                # Searching for mapped show by tvdbId
                result = search("tvdb:" + str(map['tmdb_or_tvdb_Id']))
                result['season'] = map['season']
                result['anilistId'] = show['anilistId']
            listToAdd.append(result)
        else:
            print("Searching for " + show['title'] + ' by title and year')
            result = search(show['title'] + ' ' + str(show['year']))
            if result is not None and compareDicts(result, show):
                pr("ID received from sonarr for " + show['title'])
                result['anilistId'] = show['anilistId']
                listToAdd.append(result)
            else:
                pr("ID not received from sonarr for " + show['title'])
                if not (RETRY):
                    # add to ignore list
                    addToIgnoreList(show['title'], show['anilistId'])
    for show in listToAdd:
        # hopefully "profileId" of 0 means it's not been added. "path" is None might also be a good indicator
        if 'path' in show:
            pr(show['title'] + " is already in Sonarr, checking season")
            if 'season' not in show:
                show['season'] = 1
            if show['season'] not in [i['seasonNumber'] for i in show['seasons'] if i['monitored']]:
                pr("Adding season " +
                   str(show['season']) + " to " + show['title'])
                updateSonarrSeason(show)
            else:
                pr("Season " + str(show['season']) +
                    " is already monitored for " + show['title'] + ", skipping")
            # remove show from listToAdd
            listToAdd = [x for x in listToAdd if not x == show]
    # send each item in listToAdd to add_show_to_sonarr
    for show in listToAdd:
        addShow(show)
