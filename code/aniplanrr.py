from util import *
from anilist import *
from radarr import *
from sonarr import *

# if logging is true
if LOGGING is not None:
    pr("Logging is enabled")
else:
    pr("Logging is disabled")

ignoreList = loadIgnoreList()
mapping = loadMappingList()


def main():
    if LOGGING:
        pr("Getting AniList for " + ANILIST_USERNAME)
    [aniList, aniMovieList] = getAniList(str(ANILIST_USERNAME))
    # filter anilist if anilist[2] is in ignorelist
    aniList = [x for x in aniList if x['anilistId'] not in ignoreList]
    aniMovieList = [
        x for x in aniMovieList if x['anilistId'] not in ignoreList]
    if SONARRURL:
        if LOGGING:
            pr("Getting Sonarr List")
        sonarrList = getSonarrList(SONARRURL, SONARRAPIKEY)
        if sonarrList is None:
            pr("Sonarr List is empty")
            #stop execution
            return    
        newShowList = diffDicts(aniList, sonarrList)
        if LOGGING:
            pr("Found " + str(len(newShowList)) + " new shows to add to Sonarr")
        # send each item in newShows to get_id_from_sonarr
        sendToSonarr(newShowList, mapping, sonarrList)

    if RADARRURL:
        if LOGGING:
            pr("Getting Radarr List")
        radarrList = getRadarrList(RADARRURL, RADARRAPIKEY)
        if radarrList is None:
            pr("Radarr List is empty")
            return
        newMoviesList = diffDicts(aniMovieList, radarrList)
        if LOGGING:
            pr("Found " + str(len(newMoviesList)) + " new movies to add to Radarr")
        sendToRadarr(newMoviesList, mapping, radarrList)


if __name__ == "__main__":
    main()
    pr("Sync Completed")
