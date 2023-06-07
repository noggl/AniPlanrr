import requests
from util import pr, dumpVar, LOGGING


def convertToDict(entry):
    if entry['media']['title']['english'] is not None:
        return {'title':
                entry['media']['title']['english'], 'year': entry['media']['startDate']['year'], 'anilistId': entry['media']['id']}
    else:
        return {'title':
                entry['media']['title']['romaji'], 'year': entry['media']['startDate']['year'], 'anilistId': entry['media']['id']}


def getAniList(username):
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
    response = requests.post(
        url, json={'query': query, 'variables': variables})
    # if response is not 200, throw error
    if response.status_code != 200:
        pr("Error: AniList response is not 200")
        return
    # find id of list with name "planned"
    planned_id = next((index for (index, d) in enumerate(response.json()[
                      'data']['MediaListCollection']['lists']) if d["name"] == "Planning"), None)
    entries = response.json(
    )['data']['MediaListCollection']['lists'][planned_id]

    # if name is not Planned, throw error
    if entries['name'] != "Planning":
        pr("Error: List name is not Planning")
        return
    # Create list of titles - year objects
    titleYearListTV = []
    titleYearListMovies = []
    for entry in entries['entries']:
        if entry['media']['format'] == "TV":
            titleYearListTV.append(convertToDict(entry))
        if entry['media']['format'] == "MOVIE":
            titleYearListMovies.append(convertToDict(entry))
    if LOGGING:
        dumpVar('aniListTV', titleYearListTV)
        dumpVar('aniListMovies', titleYearListMovies)
    return [titleYearListTV, titleYearListMovies]
