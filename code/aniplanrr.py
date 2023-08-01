from util import *
from anilist import *
from radarr import *
from sonarr import *

# if logging is true
if LOGGING != "False":
    pr("Logging is " + LOGGING)
else:
    pr("Logging is disabled")

ignoreList = loadIgnoreList()
mapping = loadMappingList()
if RETRY == "False" or RETRY == "Manual":
    pr("Loaded " + str(len(ignoreList)) + " items to ignore")
pr("Loaded " + str(len(mapping)) + " items to map")

def runSonarr(sonarr, aniList):
    if LOGGING != "False":
        pr("Getting Sonarr List")
    sonarrList = getSonarrList(sonarr)
    if sonarrList is None:
        pr("Sonarr List is empty")
        #stop execution
        return False

    # Remove obvious matches
    newShowList = diffDicts(aniList, sonarrList)

    # Remove less obvious matches via IDs/Mapping
    newShowList = indexSonarrList(sonarr, newShowList, mapping, sonarrList)
    if LOGGING != "False":
        pr("Found " + str(len(newShowList)) + " new shows to add to Sonarr")
    
    if SONARRIMPORTER:
        finalForm = updateSonarrImport(sonarr, newShowList, sonarrList)
        content = json.dumps(finalForm, sort_keys=True, indent=2)
        with open(webPath + 'sonarr', 'w') as f:
            f.write(content)
        pr("Wrote sonarr")
        params = {'name': 'ImportListSync'}
        requests.post(sonarr['APIURL'] + '/command/?' + sonarr['APIKEY'], json=params)
        pr("Sent command to Sonarr to import new shows")
    else:
        # send each item in newShows to get_id_from_sonarr
        sendToSonarr(sonarr, newShowList, sonarrList)

def runRadarr(radarr, aniMovieList):
    if LOGGING != "False":
        pr("Getting Radarr List")
    radarrList = getRadarrList(radarr)
    if radarrList is None:
        pr("Radarr List is empty")
        return False
    newMoviesList = diffDicts(aniMovieList, radarrList)
    newMoviesList = indexRadarrList(radarr, newMoviesList, mapping, radarrList)
    if LOGGING != "False":
        pr("Found " + str(len(newMoviesList)) + " new movies to add to Radarr")
    sendToRadarr(radarr, newMoviesList, radarrList)

def main():
    if SONARRIMPORTER:
        genIndex()
    if LOGGING != "False":
        pr("Getting AniList for " + ANILIST_USERNAME)
    [aniList, aniMovieList] = getAniList(str(ANILIST_USERNAME))
    # filter anilist if anilist[2] is in ignorelist
    if RETRY == "False" or RETRY == "Manual":
        aniList = [x for x in aniList if x['anilistId'] not in ignoreList]
        aniMovieList = [x for x in aniMovieList if x['anilistId'] not in ignoreList]
    if SONARRURL:
        sonarr = setupSonarr(SONARRURL, SONARRAPIKEY)
        if sonarr:
            runSonarr(sonarr, aniList)


    if RADARRURL:
        radarr = setupRadarr(RADARRURL, RADARRAPIKEY)
        if radarr:
            runRadarr(radarr, aniMovieList)



if __name__ == "__main__":
    main()
    pr("Sync Completed")
