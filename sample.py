from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import requests


load_dotenv(find_dotenv())


def get_token():
    token_path = "./.token"
    if os.path.exists(token_path):
        date_created = os.path.getmtime(token_path)
        token_age = datetime.now().timestamp() - date_created

        # tokens are valid for ~ 1 hr:
        # https://icd.who.int/icdapi/docs2/API-Authentication/
        if token_age < 60 * 60:
            with open(token_path, "r") as token_file:
                token = token_file.read()
                return token

    token_endpoint = os.environ.get("TOKEN_ENDPOINT")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    scope = 'icdapi_access'
    grant_type = 'client_credentials'

    # set data to post
    payload = {'client_id': client_id,
               'client_secret': client_secret,
               'scope': scope,
               'grant_type': grant_type}

    # make request
    r = requests.post(token_endpoint, data=payload, verify=False).json()
    token = r['access_token']

    with open(token_path, "w") as token_file:
        token_file.write(token)

    return token


def get_entity(entity_id, token):
    uri = f'https://id.who.int/icd/entity/{entity_id}'

    # HTTP header fields to set
    headers = {'Authorization': 'Bearer ' + token,
               'Accept': 'application/json',
               'Accept-Language': 'en',
               'API-Version': 'v2'}

    # make request           
    r = requests.get(uri, headers=headers, verify=False)

    results = r.json()
    return results


if __name__ == "__main__":
    token = get_token()
    results = get_entity(455013390, token)
    print(results)

    for child in results["child"]:
        print(child)
