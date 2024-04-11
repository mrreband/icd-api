from dataclasses import dataclass


@dataclass
class Linearization:
    name: str                   # name of the linearization (eg "mms" or "icf")
    context: str                # url to context
    oid: str                    # url to linearization
    title: dict                 # language (str) and value (str)
    latest_release_uri: str     # url to latest release
    current_release_uri: str    # id of the current release
    releases: list              # list of urls to prior releases
    base_url: str

    @staticmethod
    def uri_to_id(uri: str):
        return uri.split("/")[-2]

    @property
    def release_ids(self):
        return [self.uri_to_id(uri) for uri in self.releases]

    @property
    def current_release_id(self):
        return self.uri_to_id(self.current_release_uri)
