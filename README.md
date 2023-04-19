# AniPlanrr

Sync an AniList user's "Plan to Watch" list to Sonarr and Radarr.

This script will add any shows from your AniList planning list to Sonarr and Radarr. It will also update any shows that are already in Sonarr/Radarr to match the AniList planning list. This script will not remove shows from Sonarr/Radarr that are not in your AniList planning list, nor will it add shows to your AniList planning list.

It is highly recommended to use [RickDB/PlexMALSync](https://github.com/RickDB/PlexMALSync) to move watched shows to your watching/completed list.

# Getting Started
## Running in Docker (Recommended)
You can use the included docker-compose file to run the script in a docker container.
```
version: '3.7'
services:
  aniplanrr:
    container_name: aniplanrr
    image: ghcr.io/noggl/aniplanrr:main
    restart: unless-stopped
    environment:
      - SONARRURL=http://sonarr_url_and_port/api/   # Sonarr URL (ex: http://localhost:8989/api/)
      - SONARRAPIKEY=your_api_key                   # Sonarr API Key
      - RADARRURL=http://radarr_url_and_port/api/   # Radarr URL (ex: http://localhost:7878/api/)
      - RADARRAPIKEY=your_api_key                   # Radarr API Key
      - ANILIST_USERNAME=yourname                   # AniList Username
      - MONITOR=all                                 # Monitor Type (all, future, missing, existing, firstSeason, latestSeason, pilot) ALL IS RECOMMENDED, OTHER FLAGS MAY BE BROKEN
      - RETRY=True                                  # If True, will write failed shows to ignore file to ignore next time
      - INTERVAL=3600                               # Interval in seconds to run the script on (this will run it every hour)
    volumes:
      - '/etc/localtime:/etc/localtime:ro'
      - 'path_to_config_folder:/config'             # Config folder location, can use 'config:/config' if running from repository root
```
Once set to your liking, rename the file to `docker-compose.yaml` and run `docker-compose up` to start the container.
## Running Locally
If running locally, you will instead need to create a .env file. An example is provided in the repo as code/.env.example.
```
SONARRURL="http://192.168.1.1:8989/api/"    #Radarr URL
SONARRAPIKEY="yourapikey"                   #Radarr API Key
RADARRURL="http://192.168.1.1:7878/api/"    #Sonarr URL
RADARRAPIKEY="yourapikey"                   #Sonarr API Key
ANILIST_USERNAME="yourusername"             #AniList Username
MONITOR='all'                               #Monitor Type (all, future, missing, existing, firstSeason, latestSeason, pilot) ALL IS RECOMMENDED, OTHER FLAGS MAY BE BROKEN
RETRY=True                                  #If True, will write failed shows to ignore file to ignore next time
```
The config files will be saved to the `config` directory in the repo. You can edit the example files in that folder and remove the .example suffix to use them.

To run, you'll need to install the requirements using `pip install -r code/requirements.txt` and then run the script using `python3 code/aniplanrr.py`

## Config Files
There are 2 configuration files stored as .csv files, these are ignore.csv and mapping.csv. 
### Ignore File
The ignore file is used to store the AniList ID of shows that should be ignored. The data is stored as `Title;AniList ID`. The title is ignored, but can be used to figure out what the id is refering to. If you set RETRY to False, the script will write any shows that failed to be added to Sonarr or Radarr to the ignore file.
### Mapping File
The mapping file is used to map AniList IDs to TVDB/TMDB IDs. The script will attempt to match titles based on the AniList title, but this is not always possible or accurate, especially because AniList usually has a separate ID for each season, while TVDB does not. When an item from an AniList is being added to Sonarr/Radarr, the script will check the mapping file to see if there is a mapping for that AniList ID. If there is, it will use the mapping instead of the title. 

The data is stored as `Title;AniList ID;TVDB ID/TMDB ID;Season #`. The AniList ID is the number after `anime/` in the URL, for example, the AniList ID for [Akira (https://anilist.co/anime/47/AKIRA)](https://anilist.co/anime/47/AKIRA) is 47. The TMDB ID is the number after `movie/` but before the `-`, for example, the TMDB ID for [Akira (https://www.themoviedb.org/movie/149-akira?language=en-US)](https://www.themoviedb.org/movie/149-akira?language=en-US) is 149. The TVDB ID is not in the URL, but can be found on the show's page. For example, the TVDB ID of [Attack on Titan](https://thetvdb.com/series/attack-on-titan) is 267440. The Season # is the season of the show that the AniList ID corresponds to. 

For example, the AniList ID for [Attack on Titan Season 3](https://anilist.co/anime/99147/Attack-on-Titan-Season-3/) is 99147, but the TVDB ID for the show is 267440. The line in the mapping file would look like this:
```
Attack on Titan;99147;267440;3
```
You can have entries for each season of a show, with the same Title and TVDB ID but different AniList ID and Season Number. If you were to map the first 3 seasons of Attack on Titan, it would look like this:
```
Attack on Titan;99147;267440;3
Attack on Titan;20958;267440;2
Attack on Titan;16498;267440;1
```
If you would like to autogenerate a mapping file every time an item is added to Sonarr/Radarr, you can set `AUTO_FILL_MAPPING` to `True` in either the .env file of the docker-compose.yaml file depending on whether you're running locally or in docker. WARNING, THIS IS EXPERIEMENTAL AND MIGHT BREAK THINGS OR JUST NOT WORK!
## Thanks
Thanks to the projects [Beannsss/AniSonarrSync](https://github.com/Beannsss/AniSonarrSync) and [RickDB/PlexMALSync](https://github.com/RickDB/PlexMALSync) for the inspiration for this script.

Thanks to [AniList](https://anilist.co/),[Sonarr](https://sonarr.tv/), and [Radarr](https://radarr.video/) for providing the APIs!
