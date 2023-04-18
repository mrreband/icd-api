import time
import urllib.parse
from datetime import datetime
import os
from typing import Dict

import requests
from dataclasses import dataclass

from icd_api.icd_entity import Entity


@dataclass
class Linearisation:
    context: str            # url to context
    oid: str                # url to linearization
    title: dict             # language (str) and value (str)
    latest_release: str     # url to latest release
    releases: list          # list of urls to prior releases


class Api:
    def __init__(self):
        self.token_endpoint = os.environ.get("TOKEN_ENDPOINT")
        self.client_id = os.environ.get("CLIENT_ID")
        self.client_secret = os.environ.get("CLIENT_SECRET")
        self.base_url = os.environ.get("BASE_URL")
        self.linearization = None
        self.throttled = False

        if self.use_auth_token:
            self.token = self.get_token()
        else:
            self.token = ""

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
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': scope,
            'grant_type': grant_type,
        }

        r = requests.post(self.token_endpoint, data=payload, verify=False).json()
        token = r['access_token']

        with open(token_path, "w") as token_file:
            token_file.write(token)

        return token

    @property
    def use_auth_token(self) -> bool:
        """
        If the target server is locally deployed, authentication is not required:
        https://icd.who.int/icdapi/docs2/ICDAPI-LocalDeployment/

        :return: whether the instance contains all required info for getting an OATH2 auth token
        :rtype: bool
        """
        return self.token_endpoint is not None and self.client_id is not None and self.client_secret is not None

    @property
    def headers(self) -> dict:
        # HTTP header fields to set
        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/json',
            'Accept-Language': 'en',
            'API-Version': 'v2',
        }
        return headers

    @property
    def release_id(self):
        if self.linearization:
            return self.linearization.latest_release.split("/")[-2]
        else:
            return "2023-01"

    def get_entity(self, entity_id: str) -> Entity:
        """
        :param entity_id: id of an ICD-11 foundation entity
        :type entity_id: int
        :return: information on the specified ICD-11 foundation entity
        :rtype: Entity
        """
        uri = f"{self.base_url}/entity/{entity_id}"
        r = requests.get(uri, headers=self.headers, verify=False)
        if r.status_code == 200:
            response_data = r.json()
            return Entity.from_api(entity_id=str(entity_id), response_data=response_data, request_uri=uri)
        elif r.status_code == 404:
            return None
        else:
            raise ValueError(f"Api.get_entity -- unexpected Response {r.status_code}")

    def get_entity_full(self, entity_id: str) -> Entity:
        """
        :param entity_id: id of an ICD-11 foundation entity
        :type entity_id: int
        :return: information on the specified ICD-11 foundation entity
        :rtype: Entity
        """
        entity_obj = self.get_entity(entity_id=entity_id)
        lookup_obj = self.lookup(foundation_uri=entity_obj.foundation_uri)

        if lookup_obj is None and entity_obj is None:
            return None
        if lookup_obj is None:
            return entity_obj
        if entity_obj is None:
            return lookup_obj

        full_data = {**entity_obj.entity_data, **lookup_obj.lookup_data, "entity_id": entity_id}

        # some attributes can be found in results of both self.get_entity and self.lookup
        keys = ["inclusions", "exclusions", "foundation_child_elsewhere", "related_entities_in_perinatal_chapter"]
        if not lookup_obj.lookup_id_match:
            # if the lookup results come back with a different entity, don't use that data
            for key in keys:
                full_data[key] = getattr(entity_obj, key)
        else:
            # if the lookup is a match and it has attributes that get_entity also has, combine them
            for key in keys:
                entity_val = getattr(entity_obj, key)
                lookup_val = getattr(lookup_obj, key)
                if entity_val and lookup_val and entity_val != lookup_val:
                    print(f"{entity_id} both objs have {key}: {entity_val} != {lookup_val}")
                    full_data[key] = entity_val + lookup_val

        # make sure we're not missing anything
        if lookup_obj.synonyms:
            print(f"{entity_id} lookup_obj has synonyms")
        if entity_obj.index_terms:
            print(f"{entity_id} entity_obj has index_terms")

        full_obj = Entity(**full_data)
        full_obj.request_uris = [entity_obj.request_uri, lookup_obj.request_uri]
        full_obj.request_uri = None

        return full_obj

    def get_ancestors(self, entity_id: str, entities: list = None, depth: int = 0, nested_output: bool = True) -> list:
        """
        get all entities listed under entity.child, recursively

        :param entity_id: entity_id to look up - initially the root
        :param entities: list of already-traversed entities (initially empty)
        :param depth: current depth
        :param nested_output: whether to store child nodes in a nested structure, False = flattened
        :return: full list of all ancestry under the root
        :rtype: list
        """
        if entities is None:
            entities = []

        icd_entity = self.get_entity(entity_id=entity_id)
        icd_entity.depth = depth

        print(f"{' '*depth} get_entity: {icd_entity}")

        if nested_output:
            icd_entity.child_entities = []

        entities.append(icd_entity)

        for child_id in icd_entity.child_ids:
            existing = next(iter([e for e in entities if e.entity_id == child_id]), None)
            if existing is None:
                if nested_output:
                    self.get_ancestors(entities=icd_entity.child_entities,
                                       entity_id=child_id,
                                       depth=depth + 1,
                                       nested_output=nested_output)
                else:
                    self.get_ancestors(entities=entities,
                                       entity_id=child_id,
                                       depth=depth + 1,
                                       nested_output=nested_output)
        return entities

    def get_leaf_nodes(self, entity_id: str, entities: list = None) -> list:
        """
        get leaf entities, those with no children of their own

        :param entity_id: entity_id to look up - initially the root
        :param entities: list of already-traversed entities (initially empty)
        :return: list of all leaf node ids
        :rtype: list[str]
        """
        if entities is None:
            entities = []
        entity = self.get_entity(entity_id=entity_id)

        if not entity.child_ids:
            # this is a leaf node
            entities.append(entity_id)
        else:
            for child_id in entity.child_ids:
                existing = next(iter([e for e in entities if e == child_id]), None)
                if existing is None:
                    self.get_leaf_nodes(entities=entities, entity_id=child_id)
        return entities

    def search(self, uri) -> dict:
        r = requests.post(uri, headers=self.headers, verify=False)
        results = r.json()
        if results["error"]:
            raise ValueError(results["errorMessage"])
        return results

    def search_entities(self, search_string: str) -> list:
        """
        :param search_string:
        :return:
        """
        uri = f"{self.base_url}/entity/search?q={search_string}"
        results = self.search(uri=uri)
        return results["destinationEntities"]

    def set_linearization(self, linearization_name: str, release_id: str = None) -> Linearisation:
        """
        :return: basic information on the linearization together with the list of available releases
        :rtype: linearization
        """
        if release_id:
            uri = f"{self.base_url}/release/11/{release_id}/{linearization_name}"
        else:
            uri = f"{self.base_url}/release/11/{linearization_name}"

        r = requests.get(uri, headers=self.headers, verify=False)
        results = r.json()
        linearization = Linearisation(
            context=results["@context"],
            oid=results["@id"],
            title=results["title"],
            latest_release=results["latestRelease"],
            releases=results["release"],
        )
        self.linearization = linearization
        return linearization

    def get_entity_linearization(self, entity_id: int, linearization_name: str = "mms") -> list:
        """
        :return: a list of URIs of the entity in the available releases
        :rtype: List
        """
        uri = f"{self.base_url}/release/11/{linearization_name}/{entity_id}"
        r = requests.get(uri, headers=self.headers, verify=False)

        results = r.json()
        return results

    def get_uri(self, uri: str) -> list:
        """
        :return: a list of URIs of the entity in the available releases
        :rtype: List
        """
        url = f"{self.base_url}/{uri}"
        r = requests.get(url, headers=self.headers, verify=False)

        results = r.json()
        return results

    def get_url(self, url: str):
        """
        :return: a list of URIs of the entity in the available releases
        :rtype: List
        """
        r = requests.get(url, headers=self.headers, verify=False)

        results = r.json()
        return results

    def get_url_recurse(self, url: str, items: list, depth: int = 0):
        """
        :return: a list of URIs of the entity in the available releases
        :rtype: List
        """
        max_depth = 0
        r = requests.get(url, headers=self.headers, verify=False)
        time.sleep(0.5)

        if r.status_code == 200:
            self.throttled = False
            results = r.json()
            items.append(results)
            if depth <= max_depth:
                for child in results.get("child", []):
                    self.get_url_recurse(url=child, items=items, depth=depth + 1)
            return items
        elif r.status_code == 401:
            print("401 - throttling")
            if self.throttled:
                raise ConnectionRefusedError("response 401 twice")
            # too many requests - wait 10 minutes then try again
            self.throttled = True
            time.sleep(600)
            return self.get_url_recurse(url=url, items=items, depth=depth)
        else:
            raise ConnectionError(f"error {r.status_code}", r)

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

    def lookup(self, foundation_uri) -> Entity:
        """
        This endpoint allows looking up a foundation entity within the mms linearization
        and returns where that entity is coded in this linearization.

        If the foundation entity is included in the linearization and has a code then that linearization entity
        is returned. If the foundation entity in included in the linearization but it is a grouping without a code
        then the system will return the unspecified residual category under that grouping.

        If the entity is not included in the linearization then the system checks where that entity
        is aggregated to and then returns that entity.
        """
        foundation_id = foundation_uri.split("/")[-1]
        quoted_url = urllib.parse.quote(foundation_uri, safe='')
        uri = f"{self.base_url}/release/11/{self.release_id}/mms/lookup?foundationUri={quoted_url}"
        r = requests.get(uri, headers=self.headers, verify=False)
        if r.status_code == 200:
            response_data = r.json()
            entity = Entity.from_api(entity_id=foundation_id, response_data=response_data, request_uri=uri)
            return entity
        elif r.status_code == 404:
            return None
        else:
            raise ValueError(f"Api.lookup -- unexpected Response {r.status_code}")

    def search_linearization(self, search_string: str):
        uri = f"{self.base_url}/release/11/{self.release_id}/mms/search?q={search_string}"
        results = self.search(uri=uri)
        return results["destinationEntities"]


if __name__ == "__main__":
    api = Api()

    entity = api.get_entity("455013390")
    # for child in entity["child"]:
    #     print(child)

    search_results = api.search_entities(search_string="diabetes")
    print(search_results)
