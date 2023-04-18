import requests
from util import pr, cleanText


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
            if entry['media']['title']['english'] is not None:
                titleYearListTV.append([cleanText(
                    entry['media']['title']['english']), entry['media']['startDate']['year'], entry['media']['id']])
            else:
                titleYearListTV.append([cleanText(
                    entry['media']['title']['romaji']), entry['media']['startDate']['year'], entry['media']['id']])
        if entry['media']['format'] == "MOVIE":
            if entry['media']['title']['english'] is not None:
                titleYearListMovies.append([cleanText(
                    entry['media']['title']['english']), entry['media']['startDate']['year'], entry['media']['id']])
            else:
                titleYearListMovies.append([cleanText(
                    entry['media']['title']['romaji']), entry['media']['startDate']['year'], entry['media']['id']])
    return [titleYearListTV, titleYearListMovies]
