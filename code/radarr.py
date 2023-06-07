import requests
from util import *


def getRadarrList(RADARRURL, RADARRAPIKEY):
    response = requests.get(
        RADARRURL + "v3/movie?apikey=" + RADARRAPIKEY)
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


def addMovie(movie):
    pr("Adding " + movie['title'] + " to Radarr")
    if getRadarrTagId("fromanilist") not in movie['tags']:
        movie['tags'].append(getRadarrTagId("fromanilist"))
    movie['qualityProfileId'] = 1
    movie['path'] = '/movies/Anime/' + movie['title']
    movie['monitored'] = True
    movie['addOptions'] = {'monitor': 'movieOnly', "searchForMovie": True}
    if LOGGING:
        # write params to file
        dumpVar('addMovieParams', movie)
    response = requests.post(
        RADARRURL + 'v3/movie?apikey=' + RADARRAPIKEY, json=stripExtraKeys(movie))
    # If resposne is 201, print success
    if response.status_code == 201:
        pr(movie['title'] + " was added to Radarr")
        if AUTO_FILL_MAPPING:
            # write title, anilistId, tmdbId to mapping
            addMapping(movie)
    else:
        pr("ERRROR: " + movie['title'] + " could not be added to Radarr")
        if LOGGING:
            dumpVar('addMovieResponse', response.json())


def search(string):
    search_string = string.replace(' ', '%20')
    search_string = search_string.replace(':', '%3A')
    response = requests.get(
        RADARRURL + 'v3/movie/lookup?apikey=' + RADARRAPIKEY + '&term=' + search_string)
    #if the list has at least one element
    if len(response.json()) > 0:
        return response.json()[0]
    else:
        pr("Error: Radarr response is not array")
        if LOGGING:
            dumpVar('failedSonarrResponse', response.json())
        return


def getRadarrTagId(tag_name):
    params = {
        'label': tag_name
    }
    response = requests.get(RADARRURL + 'v3/tag?apikey=' + RADARRAPIKEY)
    tag_id = None
    # get id of tag labeled "fronAniList"
    # find id in response.json() where label = tag_name
    for i in response.json():
        if i['label'] == tag_name.lower():
            tag_id = i['id']
    # if tag_id was not found, create it
    if tag_id is None:
        response = requests.post(
            RADARRURL + 'v3/tag?apikey=' + RADARRAPIKEY, json=params)
        if response.status_code == 201:
            tag_id = response.json()['id']
    return tag_id


def sendToRadarr(newMovies, mapping, radarrList):
    listToAdd = []
    for movie in newMovies:
        if LOGGING:
            pr("Looking for ID for " + movie['title'])
        # Mapping found for Movie
        if movie['anilistId'] in [i['anilistId'] for i in mapping]:
            map = mapping[[i['anilistId']
                           for i in mapping].index(movie['anilistId'])]
            # First check if movie is in radarrList (and therefore already in radarr)
            if map['tmdb_or_tvdb_Id'] in [i['tmdbId'] for i in radarrList]:
                # mapped movie was already in radarr
                result = radarrList[[i['tmdbId']
                                     for i in radarrList].index(map['tmdb_or_tvdb_Id'])]
                result['anilistId'] = map['anilistId']
                result['season'] = map['season']
            else:
                # Searching for mapped movie by tmdbId
                result = search("tmdb:" + str(map['tmdb_or_tvdb_Id']))
                result['season'] = map['season']
                result['anilistId'] = movie['anilistId']
            listToAdd.append(result)
        # No mapping found for movie, searching by title
        else:
            print("Searching for " + movie['title'] + ' by title and year')
            result = search(movie['title'] + ' ' + str(movie['year']))
            if result is not None and compareDicts(result, movie):
                pr("ID received from radarr for " + movie['title'])
                result['anilistId'] = movie['anilistId']
                listToAdd.append(result)
            else:
                pr("ID not received from radarr for " + movie['title'])
                if not (RETRY):
                    # add to ignore list
                    addToIgnoreList(movie['title'], movie['anilistId'])  
    for movie in listToAdd:
        addMovie(movie)
