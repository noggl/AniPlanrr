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
    [aniList, aniMovieList] = getAniList(str(ANILIST_USERNAME))
    # filter anilist if anilist[2] is in ignorelist
    aniList = [x for x in aniList if x[2] not in ignoreList]
    aniMovieList = [x for x in aniMovieList if x[2] not in ignoreList]
    if SONARRURL:
        if LOGGING:
            pr("Getting Sonarr List")
        sonarrList = getSonarrList(SONARRURL, SONARRAPIKEY)
        sonarrTag = getSonarrTagId("fromanilist")
        newShowList = diffList(aniList, sonarrList)
        if LOGGING:
            pr("Found " + str(len(newShowList)) + " new shows to add to Sonarr")
        # send each item in newShows to get_id_from_sonarr
        sendToSonarr(newShowList, mapping, sonarrTag, sonarrList)
    if RADARRURL:
        if LOGGING:
            pr("Getting Radarr List")
        radarrList = getRadarrList(RADARRURL, RADARRAPIKEY)
        radarrTag = getRadarrTagId("fromanilist")
        newMoviesList = diffList(aniMovieList, radarrList)
        if LOGGING:
            pr("Found " + str(len(newMoviesList)) + " new movies to add to Radarr")

        sendToRadarr(newMoviesList, mapping, radarrTag, radarrList)


if __name__ == "__main__":
    main()
    pr("Sync Completed")
