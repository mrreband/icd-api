from dataclasses import dataclass


@dataclass
class Linearisation:
    context: str            # url to context
    oid: str                # url to linearization
    title: dict             # language (str) and value (str)
    latest_release: str     # url to latest release
    releases: list          # list of urls to prior releases

