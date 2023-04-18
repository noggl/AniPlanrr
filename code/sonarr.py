import requests
import json
import os
from util import *


def getSonarrList(SONARRURL, SONARRAPIKEY):
    response = requests.get(
        SONARRURL + "series?apikey=" + SONARRAPIKEY)
    # create list from response title and id
    if response.status_code != 200:
        pr("Error: Sonarr response is not 200")
        return
    seriesList = []
    # for each object in response
    for i in response.json():
        # if seriesType=anime
        if i['seriesType'] == "anime":
            seriesList.append([cleanText(i['title']), i['year'],
                              i['tvdbId'], i['id'], i['path'], i['seasons']])
    return seriesList


def add_show_to_sonarr(title, tvdb_id, tag, anidb_id, season=None):
    pr("Adding " + title + " to Sonarr")
    params = {
        'tvdbId': tvdb_id,
        'title': title,
        'profileId': 1,
        'seriesType': 'Anime',
        'path': '/tv/Anime/' + title,
        'seasonFolder': 'true',
        'tags': [tag]
    }
    # if season is not None, and is not 1, add season to params
    # THIS NEEDS TO GET CHANGED TO include "and season != 1"
    if season is not None:
        pr("adding unmonitored, season will be updated later")
        params['seasons'] = [{
            'seasonNumber': season,
            'monitored': 'true'
        }]
        params['addOptions'] = {'monitor': 'none',
                                "searchForMissingEpisodes": 'true'}
    else:
        params['addOptions'] = {'monitor': MONITOR,
                                "searchForMissingEpisodes": 'true'}

    # write params to file
    if LOGGING:
        dumpVar('addShowParams', params)
    response = requests.post(
        SONARRURL + 'series?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))
    # If resposne is 201, print success
    if response.status_code == 201:
        pr(title + " was added to Sonarr")
        entry = response.json()
        if season is not None:
            # wait for 4 seconds
            time.sleep(4)
            pr("season is" + str(season))
            updateSonarrSeason(entry['id'], season, tag, anidb_id)
        else:
            if AUTO_FILL_MAPPING:
                addMapping(title, tvdb_id, anidb_id, 1)
    else:
        pr("ERRROR: " + title + " could not be added to Sonarr")
        # write response to file
        if LOGGING:
            dumpVar('addShowResponse', response.json())


def get_id_from_sonarr(title, year, anidb_id):
    search_string = title.replace(' ', '%20') + '%20' + str(year)
    response = requests.get(
        SONARRURL + 'series/lookup?apikey=' + SONARRAPIKEY + '&term=' + search_string)
    sonarrTitle = cleanText(response.json()[0]['title'])
    if sonarrTitle == title.lower():
        return [response.json()[0]['title'], response.json()[0]['tvdbId'], anidb_id]
    else:
        # print the two titles
        pr("TVDB ID " + str(response.json()[0]['tvdbId']) + "(" + cleanText(
            response.json()[0]['title']) + ") seems wrong for " + title)
        # append to error file with newline if not first line
        if RETRY == "False":
            addToIgnoreList(title, anidb_id)


def updateSonarrSeason(sonarrid, season, tag, anidb_id):
    # Print variables
    pr("Updating Sonarr season")
    # Get entry from sonarr by id
    entry = requests.get(SONARRURL + 'series/' +
                         str(sonarrid) + '?apikey=' + SONARRAPIKEY).json()
    title = entry['title']
    pr("Adding " + title + " season " + str(season) + " to Sonarr")
    # change "monitored" in entry['seasons'] to true where seasonNumber = season
    for i in range(len(entry['seasons'])):
        if int(entry['seasons'][i]['seasonNumber']) == int(season):
            entry['seasons'][i]['monitored'] = True
    entry['tags'].append(tag)
    entry['monitored'] = True
    response = requests.put(
        SONARRURL + 'series/' + str(sonarrid) + '?apikey=' + SONARRAPIKEY, json=entry)
    # If resposne is 201, print success
    if response.status_code == 202:
        pr(title + " season " + str(season) + " was added to Sonarr")
        if AUTO_FILL_MAPPING:
            # write title, anidb_id, tvdbID to mappings.csv
            addMapping(title, anidb_id, entry['tvdbId'], season)
    else:
        pr("ERRROR: " + title + " season " +
           str(season) + " could not be added to Sonarr")
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


def sendToSonarr(newShows, mapping, sonarrTag, sonarrlist):
    tvdblist = []
    for show in newShows:
        if LOGGING:
            pr("Looking for ID for " + show[0])
        if show[2] in [i[1] for i in mapping]:
            map = mapping[[i[1] for i in mapping].index(show[2])]
            pr(show[0] + " is mapped to " +
               str(map[2]) + " season " + str(map[3]))
            tvdblist.append([map[0], map[2], map[1], map[3]])
        else:
            tmp = get_id_from_sonarr(show[0], show[1], show[2])
            if tmp is not None:
                pr("ID received from sonarr for " + show[0])
                tvdblist.append(tmp)
    # if id is in sonarrlist's third object, add to ignorelist
    for show in tvdblist:
        if show[1] in [i[2] for i in sonarrlist]:
            # if show has 4 items
            if len(show) == 4:
                i = sonarrlist[[i[2] for i in sonarrlist].index(show[1])]
                pr(i[0] + " is already in Sonarr, checking season")
                if str(show[3]) not in [str(season["seasonNumber"]) for season in i[5] if season["monitored"]]:
                    pr("Adding season " + str(show[3]) + " to " + show[0])
                    updateSonarrSeason(i[3], show[3], sonarrTag, show[2])
                else:
                    pr("Season " + str(show[3]) +
                       " is already monitored for " + i[0] + ", skipping")
                tvdblist = [x for x in tvdblist if not x == show]
    # send each item in tvdblist to add_show_to_sonarr
    for show in tvdblist:
        # if show length is 3
        if len(show) == 4:
            add_show_to_sonarr(show[0], show[1], sonarrTag, show[2], show[3])
        else:
            add_show_to_sonarr(show[0], show[1], sonarrTag, show[2])
