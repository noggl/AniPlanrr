
import requests
from util import *

def setupSonarr(SONARRURL, SONARRAPIKEY):
    if LOGGING == "True":
        pr("Running setupSonarr function!")
    # Define sonarr dict
    sonarr = {
        'URL': SONARRURL.rstrip("/ "),
        'APIKEY': 'apikey=' + SONARRAPIKEY.strip(),
    }
    # Add API URL based on normal URL
    sonarr['APIURL'] = sonarr['URL'] + '/api/v3'
    # Test access
    response = requests.get(sonarr['URL'] + "/ping")
    if response.status_code != 200:
        pr("Error: Can't ping Sonarr, response is" + str(response.status_code) + ", not 200. Is this the right URL? Is it up?")
        if LOGGING == "True":
            # write response to file
            dumpVar('failedSonarrResponse', response.json())
        return False
    response = requests.get(sonarr['APIURL'] + '/system/status?' + sonarr['APIKEY'])
    if response.status_code == 401:
        pr("Error: Sonarr says you are Unauthorized. Check API key? Error code: " + str(response.status_code))
        return False
    elif response.status_code != 200:
        pr("Error: Sonarr response is" + str(response.status_code) + ", not 200. This should never hit, if ping just succeeded. Is there filtering going on?")
        if LOGGING == "True":
            # write response to file
            dumpVar('failedSonarrResponse', response.json())
        return False
    answer = response.json()
    if answer['appName'] == 'Sonarr' or answer['instanceName'] == 'Sonarr':
        if LOGGING == "True":
            pr("Confirmed Sonarr instance URL and Key, returning information!")
    else:
        pr("Information seems sketch, but if it works, it works. Returning key!")
    return sonarr

    

def getSonarrList(sonarr):
    response = requests.get(sonarr['APIURL'] + "/series?" + sonarr['APIKEY'])
    # create list from response title and id
    if response.status_code != 200:
        pr("Error: Sonarr response is" + str(response.status_code) + ", not 200")
        if LOGGING == "True":
            # write response to file
            dumpVar('failedSonarrResponse', response.json())
        return
    seriesList = []
    if LOGGING == "True":
        # write response to file
        dumpVar('getSonarrResponse', response.json())
    # for each object in response
    for i in response.json():
        # if seriesType=anime
        if i['seriesType'] == "anime":
            seriesList.append(i)
    return seriesList

def setSeasons(show):
    if MONITOR == 'pilot' or MONITOR == 'firstSeason':
        pr("Setting show to monitor only the first season")
        show['season'] = 1
    if 'season' not in show or show['season'] == 1:
        pr('season not set, setting all seasons to monitored')
        for i in range(len(show['seasons'])):
            show['seasons'][i]['monitored'] = True
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
        show['addOptions'] = {'monitor': MONITOR,
                              "searchForMissingEpisodes": True}
        return show


def addShow(sonarr, show):
    pr("Adding " + show['title'] + " to Sonarr")
    show = setSeasons(show)
    if getSonarrTagId(sonarr, "fromanilist") not in show['tags']:
        show['tags'].append(getSonarrTagId(sonarr, "fromanilist"))
    # TODO, Don't use first profile, qualityprofile, or language. Allow user to set them somehow
    show['profileId'] = 1
    show['qualityProfileId'] = 1
    show['languageProfileId'] = 1
    #set type to anime
    show['seriesType'] = 'anime'
    show['path'] = SONARRANIMEPATH + show['title']
    # write show to file
    if LOGGING == "True":
        dumpVar('addShowShow', show)
    response = requests.post(
        sonarr['APIURL'] + '/series?' + sonarr['APIKEY'], json=stripExtraKeys(show))
    # If response is 201, print success
    if response.status_code == 201:
        pr(show['title'] + " was added to Sonarr")
        if LOGGING == "True":
            dumpVar('addShowResponse', response.json())
    else:
        pr("ERROR: " + show['title'] + " could not be added to Sonarr")
        # write response to file
        if LOGGING == "True":
            dumpVar('addShowResponse', response.json())


def search(sonarr, strings, year=False):
    # If it's not a list, make it a list, so we don't search each letter.
    if not isinstance(strings, list):
        strings = [strings]
    for string in strings:
        if isinstance(string, dict):
            string = str(list(string.values())[0])
        if year:
            string = string + ' ' + year
        search_string = string.replace(' ', '%20')
        search_string = search_string.replace(':', '%3A')
        url = sonarr['APIURL'] + '/series/lookup?term=' + search_string + '&' + sonarr['APIKEY']
        try:
            response = requests.get(url)
        except:
            pr("Failed to search with url: " + url)
        if LOGGING == "True":
            dumpVar('searchResponse', response.json())
        #if response is array return first element
        if len(response.json()) > 0:
            return response.json()[0]
        else:
            pr("Error: Sonarr response is not an array")
            dumpVar('failedSonarrResponse', response.json())
            continue
    return False

def getSonarrTagId(sonarr, tag_name):
    params = {
        'label': tag_name
    }
    response = requests.get(sonarr['APIURL'] + '/tag?' + sonarr['APIKEY'])
    # get id of tag labeled "fromAniList"
    tag_id = None
    for i in response.json():
        if i['label'] == tag_name.lower():
            tag_id = i['id']
    # if tag_id was not found, create it
    if tag_id is None:
        response = requests.post(
            sonarr['APIURL'] + '/tag?' + sonarr['APIKEY'], data=str(params).encode('utf-8'))
        if response.status_code == 201:
            tag_id = response.json()['id']
    return tag_id

def updateSonarrSeason(sonarr, show):
    # change "monitored" in entry['seasons'] to true where seasonNumber = season
    show = setSeasons(show)
    if getSonarrTagId(sonarr, "fromanilist") not in show['tags']:
        show['tags'].append(getSonarrTagId(sonarr, "fromanilist"))
    show['monitored'] = 'true'
    show['addOptions'] = {'monitor': MONITOR,
                          "searchForMissingEpisodes": 'true'}
    response = requests.put(
        sonarr['APIURL'] + '/series/' + str(show['id']) + '?' + sonarr['APIKEY'], json=stripExtraKeys(show))
    # If response is 201, print success
    if response.status_code == 202:
        pr(show['title'] + " season " +
           str(show['season']) + " was added to Sonarr")
    else:
        pr("ERROR: " + show['title'] + " season " +
           str(show['season']) + " could not be added to Sonarr")
        # write response to file
        if LOGGING == "True":
            dumpVar('updateSeasonResponse', response.json())

def indexSonarrList(sonarr, newShows, mapping, sonarrList):
    listToAdd = []
    for show in newShows:
        if LOGGING == "True":
                pr("Checking for existing mapping for " + show['title'])
        if show['anilistId'] in [i['anilistId'] for i in mapping]:
            # Declare result in advance
            result = False
            map = mapping[[i['anilistId']
                           for i in mapping].index(show['anilistId'])]
            pr(show['title'] + " is mapped to " +
               str(map['title']) + " season " + str(map['season']))
            # First check if show is in sonarrList (and therefore already in sonarr)
            if map['tmdb_or_tvdb_Id'] in [i['tvdbId'] for i in sonarrList]:
                if RESPECTFUL_ADDING:
                    if LOGGING == "True":
                        pr("Only looking respectfully at existing entry for " + show['title'])
                else:
                    # mapped show was already in sonarr
                    result = sonarrList[[i['tvdbId']
                                        for i in sonarrList].index(map['tmdb_or_tvdb_Id'])]
            else:
                # Searching for mapped show by tvdbId
                result = search(sonarr, "tvdb:" + str(map['tmdb_or_tvdb_Id']))
                if AUTO_FILL_MAPPING is True and result:
                    addMapping(result)
                # If there isn't a result, there's likely a type mismatch or mapping error
                if not result:
                    pr("Error: " + show['title'] + " is mapped to TVDB ID " +
                       str(map['tmdb_or_tvdb_Id']) + ", but no show was found with that ID in Sonarr")
            if result:
                listToAdd.append(result)
                result['season'] = map['season']
                result['anilistId'] = show['anilistId']
        else:
            pr("Searching Sonarr for " + show['title'] + ' by title and year')
            result = search(sonarr, show['titles'], str(show['year']))
            if result:
                if LOGGING == "True":
                    pr("Got some results!")
                    dumpVar('sonarrSearch', result)
                tvdbID = animeMatch(result, show)
                if tvdbID:
                    pr("ID received from sonarr for " + show['title'] + "with ID: " + str(tvdbID))
                    result['anilistId'] = show['anilistId']
                    listToAdd.append(result)
                    # If there's no existing mapping, and we find one, check if we should map it now.
                    if AUTO_FILL_MAPPING is True:
                        addMapping(result)
            else:
                pr("ID not received from sonarr for " + show['title'])
                if RETRY == "False":
                    # add to ignore list
                    addToIgnoreList(show['title'], show['anilistId'])
    return listToAdd

def sendToSonarr(sonarr, listToAdd, sonarrList):
    for show in listToAdd:
        # hopefully "profileId" of 0 means it's not been added. "path" is None might also be a good indicator
        if 'path' in show:
            pr(show['title'] + " is already in Sonarr, checking season")
            if 'season' not in show:
                show['season'] = 1
            if show['season'] not in [i['seasonNumber'] for i in show['seasons'] if i['monitored']]:
                pr("Adding season " +
                   str(show['season']) + " to " + show['title'])
                updateSonarrSeason(sonarr, show)
            else:
                pr("Season " + str(show['season']) +
                    " is already monitored for " + show['title'] + ", skipping")
            # remove show from listToAdd
            listToAdd = [x for x in listToAdd if not x == show]
    # send each item in listToAdd to add_show_to_sonarr
    for show in listToAdd:
        addShow(sonarr, show)

def updateSonarrImport(sonarr, listToAdd, sonarrList):
    # Create a form that will be used to fill the hosted list
    finalForm = []
    for show in listToAdd:
        entry = {
            'tvdbId': '0'
        }
        if show['tvdbId']:
            entry['tvdbId'] = str(show['tvdbId'])
            finalForm.append(entry)
        else:
            pr("Error: This show has no tvdbId?! " + show['title'])
    return finalForm
