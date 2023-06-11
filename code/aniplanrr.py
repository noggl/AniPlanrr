from util import *
from anilist import *
from radarr import *
from sonarr import *

# if logging is true
if LOGGING:
    pr("Logging is enabled")
else:
    pr("Logging is disabled")

ignoreList = loadIgnoreList()
mapping = loadMappingList()

def runSonarr(sonarr, aniList):
    if LOGGING:
        pr("Getting Sonarr List")
    sonarrList = getSonarrList(sonarr)
    if sonarrList is None:
        pr("Sonarr List is empty")
        #stop execution
        return False
    newShowList = diffDicts(aniList, sonarrList)
    if LOGGING:
        pr("Found " + str(len(newShowList)) + " new shows to add to Sonarr")
    # send each item in newShows to get_id_from_sonarr
    sendToSonarr(sonarr, newShowList, mapping, sonarrList)

def runRadarr(radarr, aniMovieList):
    if LOGGING:
        pr("Getting Radarr List")
    radarrList = getRadarrList(radarr)
    if radarrList is None:
        pr("Radarr List is empty")
        return False
    newMoviesList = diffDicts(aniMovieList, radarrList)
    if LOGGING:
        pr("Found " + str(len(newMoviesList)) + " new movies to add to Radarr")
    sendToRadarr(radarr, newMoviesList, mapping, radarrList)

def main():
    if LOGGING:
        pr("Getting AniList for " + ANILIST_USERNAME)
    [aniList, aniMovieList] = getAniList(str(ANILIST_USERNAME))
    # filter anilist if anilist[2] is in ignorelist
    aniList = [x for x in aniList if x['anilistId'] not in ignoreList]
    aniMovieList = [x for x in aniMovieList if x['anilistId'] not in ignoreList]
    # Load cursor for Anime Offline Database
    # aod = loadAOD() # loadAOD has a BUG - Requires file to already exist, will not download it
    # aodList = []
    # if LOGGING:
    #     pr("Getting AOD Listings")
    # for anime in aniList:
    #     aodList.append(searchDB(aod, anime['anilistId']))
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
