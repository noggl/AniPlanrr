import requests
from util import *

def setupRadarr(RADARRURL, RADARRAPIKEY):
    if LOGGING:
        pr("Running setupRadarr function!")
    # Define radarr dict
    radarr = {
        'URL': RADARRURL.rstrip("/ "),
        'APIKEY': 'apikey=' + RADARRAPIKEY.strip(),
    }
    # Add API URL based on normal URL
    radarr['APIURL'] = radarr['URL'] + '/api/v3'
    # Test access
    response = requests.get(radarr['URL'] + "/ping")
    if response.status_code != 200:
        pr("Error: Can't ping Radarr, response is" + str(response.status_code) + ", not 200. Is this the right URL? Is it up?")
        if LOGGING:
            # write response to file
            dumpVar('failedRadarrResponse', response.json())
        return False
    response = requests.get(radarr['APIURL'] + '/system/status?' + radarr['APIKEY'])
    if response.status_code == 401:
        pr("Error: Radarr says you are Unauthorized. Check API key? Error code: " + str(response.status_code))
        return False
    elif response.status_code != 200:
        pr("Error: Radarr response is" + str(response.status_code) + ", not 200. This should never hit, if ping just succeeded. Is there filtering going on?")
        if LOGGING:
            # write response to file
            dumpVar('failedradarrResponse', response.json())
        return False
    answer = response.json()
    if answer['appName'] == 'Radarr' or answer['instaneName'] == 'Radarr':
        if LOGGING:
            pr("Confirmed Radarr instance URL and Key, returning information!")
    else:
        pr("Information seems sketch, but if it works, it works. Returning key!")
    return radarr


def getRadarrList(radarr):
    response = requests.get(radarr['APIURL'] + "/movie?" + radarr['APIKEY'])
    # create list from response title and id
    if response.status_code != 200:
        pr("Error: Radarr response is" + str(response.status_code) + ", not 200")
        if LOGGING:
            # write response to file
            dumpVar('failedRadarrResponse', response.json())
        return
    movieList = []
    if LOGGING:
        # write response to file
        dumpVar('getRadarrResponse', response.json())
    # for each object in response
    for i in response.json():
       movieList.append(i)
    return movieList


def addMovie(radarr, movie):
    pr("Adding " + movie['title'] + " to Radarr")
    if getRadarrTagId(radarr, "fromanilist") not in movie['tags']:
        movie['tags'].append(getRadarrTagId(radarr, "fromanilist"))
    # TODO, Don't use quality profile. Allow user to set them somehow
    movie['qualityProfileId'] = 1
    movie['path'] = RADARRANIMEPATH + movie['title']
    movie['monitored'] = True
    movie['addOptions'] = {'monitor': 'movieOnly', "searchForMovie": True}
    if LOGGING:
        # write params to file
        dumpVar('addMovieParams', movie)
    response = requests.post(radarr['APIURL'] + '/movie?' + radarr['APIKEY'], json=stripExtraKeys(movie))
    # If resposne is 201, print success
    if response.status_code == 201:
        pr(movie['title'] + " was added to Radarr")
        if AUTO_FILL_MAPPING is True:
            # write title, anilistId, tmdbId to mapping
            addMapping(movie)
    else:
        pr("ERRROR: " + movie['title'] + " could not be added to Radarr")
        if LOGGING:
            dumpVar('addMovieResponse', response.json())


def search(radarr, string):
    search_string = string.replace(' ', '%20')
    search_string = search_string.replace(':', '%3A')
    response = requests.get(radarr['APIURL'] + '/movie/lookup?term=' + search_string + '&' + radarr['APIKEY'])
    #if the list has at least one element
    if len(response.json()) > 0:
        return response.json()[0]
    else:
        pr("Error: Radarr response is not array")
        if LOGGING:
            dumpVar('failedRadarrResponse', response.json())
        return


def getRadarrTagId(radarr, tag_name):
    params = {
        'label': tag_name
    }
    response = requests.get(radarr['APIURL'] + '/tag?' + radarr['APIKEY'])
    tag_id = None
    # get id of tag labeled "fronAniList"
    # find id in response.json() where label = tag_name
    for i in response.json():
        if i['label'] == tag_name.lower():
            tag_id = i['id']
    # if tag_id was not found, create it
    if tag_id is None:
        response = requests.post(
            radarr['APIURL'] + '/tag?' + radarr['APIKEY'], json=params)
        if response.status_code == 201:
            tag_id = response.json()['id']
    return tag_id


def indexRadarrList(radarr, newMovies, mapping, radarrList):
    listToAdd = []
    for movie in newMovies:
        if LOGGING:
            pr("Looking for ID for " + movie['title'])
        # Mapping found for Movie
        if movie['anilistId'] in [i['anilistId'] for i in mapping]:
            # Declare result in advance
            result = False
            map = mapping[[i['anilistId']
                           for i in mapping].index(movie['anilistId'])]
            # First check if movie is in radarrList (and therefore already in radarr)
            if map['tmdb_or_tvdb_Id'] in [i['tmdbId'] for i in radarrList]:
                if RESPECTFUL_ADDING:
                    if LOGGING:
                        pr("Only looking respectfully at existing entry for " + show['title'])
                else:
                    # mapped movie was already in radarr
                    result = radarrList[[i['tmdbId']
                                        for i in radarrList].index(map['tmdb_or_tvdb_Id'])]
                    result['anilistId'] = map['anilistId']
                    result['season'] = map['season']
            else:
                # Searching for mapped movie by tmdbId
                result = search(radarr, "tmdb:" + str(map['tmdb_or_tvdb_Id']))
                result['season'] = map['season']
                result['anilistId'] = movie['anilistId']
            if result:
                listToAdd.append(result)
        # No mapping found for movie, searching by title
        else:
            print("Searching for " + movie['title'] + ' by title and year')
            result = search(radarr, movie['title'] + ' ' + str(movie['year']))
            if result is not None and compareDicts(result, movie):
                pr("ID received from radarr for " + movie['title'])
                result['anilistId'] = movie['anilistId']
                listToAdd.append(result)
            else:
                pr("ID not received from radarr for " + movie['title'])
                if not (RETRY):
                    # add to ignore list
                    addToIgnoreList(movie['title'], movie['anilistId'])  
    return listToAdd

def sendToRadarr(radarr, listToAdd, radarrList):
    for movie in listToAdd:
        addMovie(radarr, movie)
