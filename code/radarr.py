import requests
import json
import os
from util import *


def getRadarrMovies(RADARRURL, RADARRAPIKEY):
    response = requests.get(
        RADARRURL + "v3/movie?apikey=" + RADARRAPIKEY)
    # create list from response title and id
    if response.status_code != 200:
        pr("Error: Radarr response is not 200")
        return
    movieList = []
    if LOGGING:
        # write response to file
        dumpVar('getRadarrResponse', response.json())
    for i in response.json():
        movieList.append([cleanText(i['title']), i['year'], i['tmdbId']])
    return movieList


def add_movie_to_radarr(title, tmdb_id, tag, anidb_id):
    pr("Adding " + title + " to Radarr")
    # print variables

    params = {
        'tmdbId': tmdb_id,
        'title': title,
        'qualityProfileId': 1,
        'path': '/movies/Anime/' + title,
        'minimumAvailability': 'released',
        'tags': [tag],
        'monitored': True,
        'addOptions': {'monitor': 'movieOnly', "searchForMovie": True}
    }
    if LOGGING:
        # write params to file
        dumpVar('addMovieParams', params)
    response = requests.post(
        RADARRURL + 'v3/movie?apikey=' + RADARRAPIKEY, json=params)
    # If resposne is 201, print success
    if response.status_code == 201:
        pr(title + " was added to Radarr")
        if AUTO_FILL_MAPPING:
            # write title, anidb_id, tvdbID to mapping
            addMapping(title, anidb_id, tmdb_id, 1)
    else:
        pr("ERRROR: " + title + " could not be added to Radarr")
        dumpVar('addMovieResponse', response.json())


def get_id_from_radarr(title, year, anidb_id):
    search_string = title.replace(' ', '%20') + '%20' + str(year)
    # pr(search_string)
    response = requests.get(
        RADARRURL + 'v3/movie/lookup?apikey=' + RADARRAPIKEY + '&term=' + search_string)
    # pr(response.json())
    radarrTitle = cleanText(response.json()[0]['title'])
    if radarrTitle == title.lower():
        return [response.json()[0]['title'], response.json()[0]['tmdbId'], anidb_id]
    else:
        # print the two titles
        pr("TMDB ID " + str(response.json()[0]['tmdbId']) + "(" + cleanText(
            response.json()[0]['title']) + ") seems wrong for " + title)


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


def sendToRadarr(newMovies, mapping, radarrTag, radarrList):
    moviedblist = []
    for movie in newMovies:
        if LOGGING:
            pr("Looking for ID for " + movie[0])
        if movie[2] in [i[1] for i in mapping]:
            map = mapping[[i[1] for i in mapping].index(movie[2])]
            pr(movie[0] + " is mapped to " + str(map[2]))
            moviedblist.append([map[0], map[2], map[1]])
        else:
            tmp = get_id_from_radarr(movie[0], movie[1], movie[2])
            if tmp is not None:
                pr("ID received from radarr for " + movie[0])
                moviedblist.append(tmp)

    for movie in moviedblist:
        if movie[1] in [i[2] for i in radarrList]:
            pr(movie[0] + " is already in Radarr, skipping")
        else:
            add_movie_to_radarr(movie[0], movie[1], radarrTag, movie[2])
