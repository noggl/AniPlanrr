# Here we define our query as a multi-line string
import time
import requests
import json
import os
from dotenv import load_dotenv
import re

#check if there is a .env file
if os.path.exists('.env'):
    load_dotenv()
    SONARRURL = os.getenv('SONARRURL')
    SONARRAPIKEY = os.getenv('SONARRAPIKEY')
    ANILIST_USERNAME = os.getenv('ANILIST_USERNAME')
    MONITOR = os.getenv('MONITOR')
    RETRY = os.getenv('RETRY')
    LOGGING = os.getenv('LOGGING')
else:
    SONARRURL = os.environ['SONARRURL']
    SONARRAPIKEY = os.environ['SONARRAPIKEY']
    ANILIST_USERNAME = os.environ['ANILIST_USERNAME']
    MONITOR = os.environ['MONITOR']
    RETRY = os.environ['RETRY']
    LOGGING=os.environ['LOGGING']

#if logging is true
if LOGGING is not None:
    print("Logging is enabled")
else:
    print("Logging is disabled")

# Create list of titles - year objects from ignorelist.txt if it exists
ignoreList = []
if os.path.exists('ignore.csv'):
    with open('ignore.csv', 'r') as f:
        for line in f:
            arr = line.strip().split(';')
            ignoreList.append(int(arr[1]))

#import custom mapping array from mapping.csv if it exists
mapping = []
if os.path.exists('mapping.csv'):
    with open('mapping.csv', 'r') as f:
        for line in f:
            arr = line.strip().split(';')
            mapping.append([arr[0],int(arr[1]),int(arr[2]),int(arr[3])])

def addToIgnoreList(title, id):
    #if id isn't already in ignorelist
    if id not in ignoreList:
        #add id to ignorelist
        print("Adding " + title + " to ignore list")
        with open('ignore.csv', 'a') as f:
        # if file is not empty, add newline
            if os.stat('ignore.csv').st_size != 0:
                f.write('\n')
            f.write(title + ';' + str(id))
    else:
        print(title + " is already in ignore list")

def cleanText(string):
    return re.sub(r'[^\w\s]', '', str(string)).lower()

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
    # find id of list with name "planned"
    planned_id = next((index for (index, d) in enumerate(response.json()['data']['MediaListCollection']['lists']) if d["name"] == "Planning"), None)
    entries = response.json()['data']['MediaListCollection']['lists'][planned_id];
    
    #if name is not Planned, throw error
    if entries['name'] != "Planning":
        print("Error: List name is not Planning")
        return
    # Create list of titles - year objects
    titleYearList = []
    for entry in entries['entries']:
        if entry['media']['format'] == format:
            if entry['media']['title']['english'] is not None:
                titleYearList.append([cleanText(entry['media']['title']['english']), entry['media']['startDate']['year'],entry['media']['id']])
            else:
                titleYearList.append([cleanText(entry['media']['title']['romaji']), entry['media']['startDate']['year'],entry['media']['id']])
    return titleYearList

def getSonarrSeries(SONARRURL, SONARRAPIKEY):
    response = requests.get(
    SONARRURL + "series?apikey=" + SONARRAPIKEY)
    #create list from response title and id
    seriesList = []
    #for first object in response
    for i in response.json():
        #if seriesType=anime
        if i['seriesType'] == "anime":
            with open('serie.json', 'w') as outfile:
                json.dump(i, outfile)
            seriesList.append([cleanText(i['title'].lower()), i['year'],i['tvdbId'],i['id'],i['path'],i['seasons']])
    return seriesList

def getListDifference(list1, list2):
    #ignore third element of every object
    list1_strip = [i[:2] for i in list1]
    list2_strip = [i[:2] for i in list2]
    #Get index of every object in list1 that is not in list2
    diff=[]
    for i in list1_strip:
        if i not in list2_strip:
            diff.append(list1_strip.index(i))
    
    #return list of objects in list1 that are not in list2
    return [list1[i] for i in diff]
    

def add_show_to_sonarr(title,tvdb_id,tag,season=None):
    print("Adding " + title + " to Sonarr")
    params = {
        'tvdbId': tvdb_id,
        'title': title,
        'profileId': 1,
        'seriesType': 'Anime',
        'path': '/tv/Anime/' + title,
        'seasonFolder': 'true',
        'tags': [tag]
    }
    if season is not None:
        print("adding unmonitored, season will be updated later")
        params['seasons'] = [{
        'seasonNumber': season,
        'monitored': 'true'
    }]
        params['addOptions']= {'monitor': 'none', "searchForMissingEpisodes": 'true'}
    else:
        params['addOptions']= {'monitor': MONITOR, "searchForMissingEpisodes": 'true'}

    #write params to file
    with open('params.json', 'w') as outfile:
            json.dump(params, outfile)
    response = requests.post(SONARRURL + 'series?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))
    # If resposne is 201, print success
    if response.status_code == 201:
        print(title + " was added to Sonarr")
        if season is not None:
            entry=response.json()
            #wait for 10 seconds
            time.sleep(4)
            updateSonarrSeason(entry['title'],entry['tvdbId'],season,entry['id'],entry['path'],entry['tags'])
    else:
        print("ERRROR: " + title + " could not be added to Sonarr")
        #write response to file
        with open('response.json', 'w') as outfile:
            json.dump(response.json(), outfile)
        #print response.errorMessage
        


def get_id_from_sonarr(title, year,anidb_id):
    search_string = title.replace(' ', '%20') + '%20' + str(year)
    #print(search_string)
    response = requests.get(
        SONARRURL + 'series/lookup?apikey=' + SONARRAPIKEY + '&term=' + search_string)
    sonarrTitle=cleanText(response.json()[0]['title'])
    if sonarrTitle == title.lower():
        return [response.json()[0]['title'], response.json()[0]['tvdbId']]
    else:
        #print the two titles
        print("TVDB ID " + str(response.json()[0]['tvdbId']) + "(" + cleanText(response.json()[0]['title']) + ") seems wrong for " + title)
        #append to error file with newline if not first line
        if RETRY == "False":
            addToIgnoreList(title, anidb_id)

def updateSonarrSeason(title,tvdb_id,season,sonarrid,sonarrpath,tags=None):
    print("Adding " + title + " season " + str(season) + " to Sonarr")
    params = {
    'id': sonarrid,
    'tvdbId': tvdb_id,
    'profileId': 1,
    'path': sonarrpath,
    'seriesType': 'Anime',
    'seasons': [{
        'seasonNumber': season,
        'monitored': 'true'
    }],
    'addOptions': {'searchForMissingEpisodes': 'false'}
    }
    if tags is not None:
        params['tags'] = tags
    response = requests.put(SONARRURL + 'series/' + str(sonarrid) + '?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))
    # If resposne is 201, print success
    if response.status_code == 202:
        print(title + " season " + str(season) + " was added to Sonarr")
    else:
        print("ERRROR: " + title + " season " + str(season) + " could not be added to Sonarr")
        #write response to file
        with open('response.json', 'w') as outfile:
            json.dump(response.json(), outfile)
        #print response.errorMessage



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

if os.path.exists('.env'):
    print("Found .env file, loading variables")
else:
    print("No .env file found, loading variables from environment")
    
def main():
    if LOGGING:
            print("Getting AniList for " + ANILIST_USERNAME)
    anilist = getAniList(str(ANILIST_USERNAME), "TV");
    #filter anilist if anilist[2] is in ignorelist
    anilist = [x for x in anilist if x[2] not in ignoreList]
    if LOGGING:
            print("Getting Sonarr List")
    sonarrlist = getSonarrSeries(SONARRURL, SONARRAPIKEY);
    newShows = getListDifference(anilist, sonarrlist);
    if LOGGING:
            print("Found " + str(len(newShows)) + " new shows to add to Sonarr")
    if LOGGING:
        with open('newShows.json', 'w') as outfile:
            json.dump(newShows, outfile)
        with open('sonarrlist.json', 'w') as outfile:
            json.dump(sonarrlist, outfile)
        with open('anilist.json', 'w') as outfile:
            json.dump(anilist, outfile)
        with open('ignorelist.json', 'w') as outfile:
            json.dump(ignoreList, outfile)
        with open('mapping.json', 'w') as outfile:
            json.dump(mapping, outfile)

    tag=getTagId("fromanilist")

    #send each item in newShows to get_id_from_sonarr
    tvdblist = []
    for show in newShows:
        if LOGGING:
            print("Looking for ID for " + show[0])
        if show[2] in [i[1] for i in mapping]:
            map=mapping[[i[1] for i in mapping].index(show[2])]
            print(show[0] + " is mapped to " + str(map[2]) + " season " + str(map[3]))
            tvdblist.append([map[0],map[2],map[3]])
        else:
            tmp = get_id_from_sonarr(show[0], show[1], show[2])
            if tmp is not None:
                print("ID received from sonarr " + show[0])
                tvdblist.append(tmp)

    #if id is in sonarrlist's third object, add to ignorelist
    for show in tvdblist:
        if show[1] in [i[2] for i in sonarrlist]:
            print(show[0] + " is already in Sonarr, checking season")
            i=sonarrlist[[i[2] for i in sonarrlist].index(show[1])]
            if str(show[2]) not in [str(season["seasonNumber"]) for season in i[5]]:
                print("Adding season " + str(show[2]) + " to " + show[0])
                updateSonarrSeason(show[0],show[1],show[2],i[3],i[4])
            else:
                print("Season " + str(show[2]) + " is already monitored for " + show[0] +", skipping")
            tvdblist= [x for x in tvdblist if not x==show]
    #send each item in tvdblist to add_show_to_sonarr
    for show in tvdblist:
        #if show length is 3
        if len(show) == 3:
            add_show_to_sonarr(show[0],show[1],tag,show[2])
        else:
            add_show_to_sonarr(show[0],show[1],tag)



if __name__ == "__main__":
    main()
    print("Sync Completed")