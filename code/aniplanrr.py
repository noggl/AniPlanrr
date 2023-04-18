import os
from dotenv import load_dotenv
from util import *
from anilist import *
from radarr import *
from sonarr import *

# if logging is true
if LOGGING is not None:
    pr("Logging is enabled")
    # create log folder
    if not os.path.exists('log'):
        os.makedirs('log')
else:
    pr("Logging is disabled")

ignoreList = loadIgnoreList()
mapping = loadMappingList()


def main():
    if LOGGING:
        pr("Getting AniList for " + ANILIST_USERNAME)
    [anilist, animovielist] = getAniList(str(ANILIST_USERNAME))
    # filter anilist if anilist[2] is in ignorelist
    anilist = [x for x in anilist if x[2] not in ignoreList]
    animovielist = [x for x in animovielist if x[2] not in ignoreList]
    if SONARRURL:
        if LOGGING:
            pr("Getting Sonarr List")
        sonarrlist = getSonarrSeries(SONARRURL, SONARRAPIKEY)
        newShows = getListDifference(anilist, sonarrlist)
        sonarrTag = getSonarrTagId("fromanilist")
        if LOGGING:
            pr("Found " + str(len(newShows)) + " new shows to add to Sonarr")
        # send each item in newShows to get_id_from_sonarr
        sendToSonarr(newShows, mapping, sonarrTag, sonarrlist)
    if RADARRURL:
        if LOGGING:
            pr("Getting Radarr List")
        radarrlist = getRadarrMovies(RADARRURL, RADARRAPIKEY)
        newMovies = getListDifference(animovielist, radarrlist)
        if LOGGING:
            pr("Found " + str(len(newMovies)) + " new movies to add to Radarr")
        radarrTag = getRadarrTagId("fromanilist")
        sendToRadarr(newMovies, mapping, radarrTag, radarrlist)


if __name__ == "__main__":
    main()
    pr("Sync Completed")
