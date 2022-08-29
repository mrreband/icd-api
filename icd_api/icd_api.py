from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import requests


load_dotenv(find_dotenv())


class Api:
    def __init__(self):
        self.token_endpoint = os.environ.get("TOKEN_ENDPOINT")
        self.client_id = os.environ.get("CLIENT_ID")
        self.client_secret = os.environ.get("CLIENT_SECRET")
        self.base_url = os.environ.get("BASE_URL")
        self.token = self.get_token()
        self.headers = self.get_headers()

    def get_token(self):
        token_path = "../.token"
        if os.path.exists(token_path):
            date_created = os.path.getmtime(token_path)
            token_age = datetime.now().timestamp() - date_created

            # tokens are valid for ~ 1 hr:
            # https://icd.who.int/icdapi/docs2/API-Authentication/
            if token_age < 60 * 60:
                with open(token_path, "r") as token_file:
                    token = token_file.read()
                    return token

        scope = 'icdapi_access'
        grant_type = 'client_credentials'
        payload = {'client_id': self.client_id,
                   'client_secret': self.client_secret,
                   'scope': scope,
                   'grant_type': grant_type}

        r = requests.post(self.token_endpoint, data=payload, verify=False).json()
        token = r['access_token']

        with open(token_path, "w") as token_file:
            token_file.write(token)

        return token

    def get_headers(self):
        # HTTP header fields to set
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/json',
                   'Accept-Language': 'en',
                   'API-Version': 'v2'}
        return headers

    def get_entity(self, entity_id):
        uri = f"{self.base_url}/entity/{entity_id}"
        r = requests.get(uri, headers=self.headers, verify=False)

        results = r.json()
        return results

    def search_entities(self, search_string):
        uri = f"{self.base_url}/entity/search?q={search_string}"
        r = requests.post(uri, headers=self.headers, verify=False)
        results = r.json()
        if results["error"]:
            raise ValueError(results["errorMessage"])
        return results["destinationEntities"]


if __name__ == "__main__":
    api = Api()

    entity = api.get_entity(455013390)
    # for child in entity["child"]:
    #     print(child)

    search_results = api.search_entities(search_string="diabetes")
    print(search_results)
