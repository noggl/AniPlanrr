# Here we define our query as a multi-line string
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

SONARRURL = os.getenv('SONARRURL')
SONARRAPIKEY = os.getenv('SONARRAPIKEY')
ANILIST_USERNAME = os.getenv('ANILIST_USERNAME')
MONITOR_ALL = os.getenv('MONITOR_ALL')

def getAniList(username,format):
    query = query = """
                query ($username: String) {
                MediaListCollection(userName: $username, type: ANIME) {
                    lists {
                    name
                    entries {
                        media{
                        id
                        format
                        startDate {
                            year
                        }
                        endDate {
                            year
                        }
                        title {
                            romaji
                            english
                        }
                        }
                    }
                    }
                }
                }
    """

    # Define our query variables and values that will be used in the query request
    variables = {
        'username': username
    }
    url = 'https://graphql.anilist.co'

    # Make the HTTP Api request
    response = requests.post(url, json={'query': query, 'variables': variables})
    entries = response.json()['data']['MediaListCollection']['lists'][3];
    # Create list of titles - year objects
    titleYearList = []
    for entry in entries['entries']:
        if entry['media']['format'] == format:
            if entry['media']['title']['english'] is not None:
                titleYearList.append([entry['media']['title']['english'].lower(), entry['media']['startDate']['year']])
            else:
                titleYearList.append([entry['media']['title']['romaji'].lower(), entry['media']['startDate']['year']])
    return titleYearList

def getSonarrSeries(SONARRURL, SONARRAPIKEY):
    response = requests.get(
    SONARRURL + "series?apikey=" + SONARRAPIKEY)
    #create list from response title and id
    seriesList = []
    for i in response.json():
        #if seriesType=anime
        if i['seriesType'] == "anime":
            seriesList.append([i['title'].lower(), i['year']])
    return seriesList

def getListDifference(list1, list2):
    return [item for item in list1 if item not in list2]

def add_show_to_sonarr(title, tvdb_id,tag):
    #if Monitor All is true, set monitored to true
    if MONITOR_ALL == "true":
        monitored = "all"
    else:
        monitored = "pilot"
    params = {
        'tvdbId': tvdb_id,
        'title': title,
        'profileId': 1,
        'seriesType': 'Anime',
        'path': '/tv/Anime/' + title,
        'monitored': 'true',
        'seasonFolder': 'true',
        'tags': [tag],
        'addOptions': {'monitored': monitored, "searchForMissingEpisodes": 'true'}
    }
    #write params to file
    with open('params.json', 'w') as outfile:
        json.dump(params, outfile)
    response = requests.post(SONARRURL + 'series?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))
    # If resposne is 201, print success
    if response.status_code == 201:
        print(title + " was added to Sonarr")
    else:
        print("Error: " + title + " was not added to Sonarr")

def get_id_from_sonarr(title, year):
    search_string = title.replace(' ', '%20') + '%20' + str(year)
    #print(search_string)
    response = requests.get(
        SONARRURL + 'series/lookup?apikey=' + SONARRAPIKEY + '&term=' + search_string)
    if response.json()[0]['title'].lower() == title:
        return [response.json()[0]['title'], response.json()[0]['tvdbId'],response.json()[0]['seasons']]
    else:
        #print the two titles
        print(str(title) + " and " + str(response.json()[0]['title']).lower() + " dont match")

def getTagId(tag_name):
    params = {
        'label': tag_name
    }
    response = requests.get(SONARRURL + 'tag?apikey=' + SONARRAPIKEY)
    #get id of tag labeled "fronAniList"
    for i in response.json():
        if i['label'] == tag_name.lower():
            tag_id = i['id']
    # if tag_id was not found, create it
    if tag_id is None:
        response = requests.post(SONARRURL + 'tag?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))
        if response.status_code == 201:
            for i in response.json():
                if i['label'] == tag_name.lower():
                    tag_id = i['id']
    return tag_id

    

anilist = getAniList(ANILIST_USERNAME, "TV");
#write anilist to file
with open('anilist.json', 'w') as outfile:
    json.dump(anilist, outfile)
sonarrlist = getSonarrSeries(SONARRURL, SONARRAPIKEY);
#write Sonarrlist to sonarrlist.json
with open('sonarrlist.json', 'w') as outfile:
    json.dump(sonarrlist, outfile)
newShows = getListDifference(anilist, sonarrlist);
#write newShows to newShows.json
with open('newShows.json', 'w') as outfile:
    json.dump(newShows, outfile)

tag=getTagId("fromanilist")

#send each item in newShows to get_id_from_sonarr
tvdblist = []
for show in newShows:
    tmp = get_id_from_sonarr(show[0], show[1])
    if tmp is not None:
        tvdblist.append(tmp)

#send each item in tvdblist to add_show_to_sonarr
for show in tvdblist:
    add_show_to_sonarr(show[0],show[1],tag)

