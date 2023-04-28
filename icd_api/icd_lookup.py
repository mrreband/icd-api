from dataclasses import dataclass
from typing import Dict, List

lookup_known_keys = [
    "@context", "@id", "title", "definition", "longDefinition", "fullySpecifiedName", "diagnosticCriteria",
    "source", "code", "codingNote", "blockId", "codeRange", "classKind", "child", "parent", "ancestor",
    "descendant", "foundationChildElsewhere", "indexTerm", "inclusion", "exclusion", "postcoordinationScale",
    "browserUrl",
]


def get_entity_id(uri: str):
    return uri.split("/")[-1]


def get_foundation_uri(entity_id: str):
    return f"http://id.who.int/icd/entity/{entity_id}"


def get_linearization_uri(entity_id: str, linearization: str):
    return f"http://id.who.int/icd/release/11/beta/{linearization}/{entity_id}"


def get_mms_uri(entity_id: str):
    return get_linearization_uri(entity_id=entity_id, linearization="mms")


@dataclass
class ICDLookup:
    foundation_uri: str
    title: str
    definition: str = None
    long_definition: str = None
    fully_specified_name: str = None
    diagnostic_criteria: str = None
    source: str = None
    code: str = None
    coding_note: str = None
    block_id: str = None
    code_range: str = None
    class_kind: str = None
    parent: list = None
    child: list = None
    ancestor: list = None
    descendent: list = None
    foundation_child_elsewhere: list = None
    index_term: list = None
    inclusion: list = None
    exclusion: list = None
    post_coordination_scale: list = None
    browser_url: str = None

    # place to store any response data not itemized above
    other: dict = None

    def __repr__(self):
        response = f"Lookup {self.entity_id} - {self.title}"
        if self.code:
            response += f" (mms {self.class_kind} {self.code})"
        return response

    @property
    def request_type(self) -> str:
        return "lookup"

    @property
    def entity_id(self) -> str:
        return self.foundation_uri.split("/")[-1]

    @property
    def linearization_release_uri(self) -> str:
        return get_mms_uri(self.entity_id)

    @property
    def parent_uris(self) -> list[str]:
        return self.parent

    @property
    def parent_ids(self) -> list[str]:
        return [get_entity_id(uri=uri) for uri in self.parent_uris]

    @property
    def parent_count(self) -> int:
        return len(self.parent_ids)

    @property
    def child_uris(self) -> list[str]:
        return self.child

    @property
    def child_ids(self) -> list[str]:
        return [get_entity_id(uri=uri) for uri in self.child_uris]

    @property
    def child_count(self) -> int:
        return len(self.child_ids)

    @classmethod
    def from_api(cls, response_data: dict):
        params = dict((k, v) for k, v in response_data.items() if k in lookup_known_keys)
        other = dict((k, v) for k, v in response_data.items() if k not in lookup_known_keys)
        return cls(**params, other=other)
