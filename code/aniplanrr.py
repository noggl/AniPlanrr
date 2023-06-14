from util import *
from anilist import *
from radarr import *
from sonarr import *

# if logging is true
if LOGGING == "True":
    pr("Logging is enabled")
else:
    pr("Logging is disabled")

ignoreList = loadIgnoreList()
mapping = loadMappingList()
if RETRY == "False" or RETRY == "Manual":
    pr("Loaded " + str(len(ignoreList)) + " items to ignore")
pr("Loaded " + str(len(mapping)) + " items to map")

def runSonarr(sonarr, aniList):
    if LOGGING == "True":
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
    if LOGGING == "True":
        pr("Found " + str(len(newShowList)) + " new shows to add to Sonarr")
    
    # send each item in newShows to get_id_from_sonarr
    sendToSonarr(sonarr, newShowList, sonarrList)

def runRadarr(radarr, aniMovieList):
    if LOGGING == "True":
        pr("Getting Radarr List")
    radarrList = getRadarrList(radarr)
    if radarrList is None:
        pr("Radarr List is empty")
        return False
    newMoviesList = diffDicts(aniMovieList, radarrList)
    newMoviesList = indexRadarrList(radarr, newMoviesList, mapping, radarrList)
    if LOGGING == "True":
        pr("Found " + str(len(newMoviesList)) + " new movies to add to Radarr")
    sendToRadarr(radarr, newMoviesList, radarrList)

def main():
    if LOGGING == "True":
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
