import urllib.parse
from datetime import datetime
import os
import requests

from icd_api.linearisation import Linearisation


class Api:
    def __init__(self):
        self.token_endpoint = os.environ.get("TOKEN_ENDPOINT")
        self.client_id = os.environ.get("CLIENT_ID")
        self.client_secret = os.environ.get("CLIENT_SECRET")
        self.base_url = os.environ.get("BASE_URL")
        self.token = self.get_token()
        self.linearisation = None

    def get_token(self) -> str:
        """
        :return: authorization token, valid for up to one hour, may be cached in a local `.token` file
        :rtype: str
        """
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

    @property
    def headers(self) -> dict:
        # HTTP header fields to set
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/json',
                   'Accept-Language': 'en',
                   'API-Version': 'v2'}
        return headers

    @property
    def release_id(self):
        if self.linearisation:
            return self.linearisation.latest_release.split("/")[-2]
        else:
            return "2022-02"

    def get_entity(self, entity_id: int) -> dict:
        """
        :param entity_id: id of an ICD-11 foundation entity
        :type entity_id: int
        :return: information on the specified ICD-11 foundation entity
        :rtype: dict
        """
        uri = f"{self.base_url}/entity/{entity_id}"
        r = requests.get(uri, headers=self.headers, verify=False)

        results = r.json()
        return results

    def search_entities(self, search_string: str) -> list:
        """
        :param search_string:
        :return:
        """
        uri = f"{self.base_url}/entity/search?q={search_string}"
        r = requests.post(uri, headers=self.headers, verify=False)
        results = r.json()
        if results["error"]:
            raise ValueError(results["errorMessage"])
        return results["destinationEntities"]

    def set_linearisation(self, linearisation_name: str, release_id: str = None) -> Linearisation:
        """
        :return: basic information on the linearisation together with the list of available releases
        :rtype: Linearisation
        """
        if release_id:
            uri = f"{self.base_url}/release/11/{release_id}/{linearisation_name}"
        else:
            uri = f"{self.base_url}/release/11/{linearisation_name}"

        r = requests.get(uri, headers=self.headers, verify=False)
        results = r.json()
        linearisation = Linearisation(context=results["@context"],
                                      oid=results["@id"],
                                      title=results["title"],
                                      latest_release=results["latestRelease"],
                                      releases=results["release"])
        self.linearisation = linearisation
        return linearisation

    def get_entity_linearization(self, entity_id: int, linearisation_name: str = "mms"):
        """
        :return: a list of URIs of the entity in the available releases
        :rtype: List
        """
        uri = f"{self.base_url}/release/11/{linearisation_name}/{entity_id}"
        r = requests.get(uri, headers=self.headers, verify=False)

        results = r.json()
        return results

    def get_code(self, icd_version: int, code: str):
        """
        :return: a list of URIs of the entity in the available releases
        :rtype: List
        """
        if icd_version == 10:
            uri = f"{self.base_url}/release/10/{code}"
        else:
            quoted_code = urllib.parse.quote(code, safe="")
            uri = f"{self.base_url}/release/11/{self.release_id}/mms/codeinfo/{quoted_code}?flexiblemode=true"
        r = requests.get(uri, headers=self.headers, verify=False)

        results = r.json()
        return results

    def lookup(self, foundation_uri):
        """
        This endpoint allows looking up a foundation entity within a linearization
        and returns where that entity is coded in this linearization.

        If the foundation entity is included in the linearization and has a code then that linearization entity
        is returned. If the foundation entity in included in the linearization but it is a grouping without a code
        then the system will return the unspecified residual category under that grouping.

        If the entity is not included in the linearization then the system checks where that entity
        is aggregated to and then returns that entity.
        """
        quoted_url = urllib.parse.quote(foundation_uri, safe='')
        uri = f"{self.base_url}/release/11/{self.release_id}/mms/lookup?foundationUri={quoted_url}"
        r = requests.get(uri, headers=self.headers, verify=False)
        results = r.json()
        return results


if __name__ == "__main__":
    api = Api()

    entity = api.get_entity(455013390)
    # for child in entity["child"]:
    #     print(child)

    search_results = api.search_entities(search_string="diabetes")
    print(search_results)
