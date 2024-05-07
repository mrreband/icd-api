import json
from dataclasses import dataclass, field
from typing import Optional

from icd_api.icd_util import get_foundation_uri, get_entity_id, get_params_dicts, flatten_labels

entity_known_keys = [
    "title", "definition", "longDefinition", "fullySpecifiedName", "diagnosticCriteria", "child", "parent",
    "ancestor", "descendant", "synonym", "narrowerTerm", "inclusion", "exclusion", "browserUrl",
]


@dataclass
class ICDEntity:
    entity_id: str
    title: str
    definition: Optional[str] = None
    long_definition: Optional[str] = None
    fully_specified_name: Optional[str] = None
    diagnostic_criteria: Optional[str] = None
    child: list = field(default_factory=list)
    parent: list = field(default_factory=list)
    ancestor: list = field(default_factory=list)
    descendant: list = field(default_factory=list)
    synonym: list = field(default_factory=list)
    narrower_term: list = field(default_factory=list)
    inclusion: list = field(default_factory=list)
    exclusion: list = field(default_factory=list)
    browser_url: Optional[str] = None

    # custom attributes
    entity_residual: Optional[str] = None           # if the uri ends with unspecified or other, store that here
    residuals: dict = field(default_factory=dict)   # results of icd_api.get_residuals go here

    # place to store any response data not itemized above
    other: dict = field(default_factory=dict)

    @property
    def request_type(self):
        return "entity"

    @property
    def foundation_uri(self):
        return get_foundation_uri(entity_id=self.entity_id)

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
        return self.child or []

    @property
    def child_ids(self) -> list[str]:
        return [get_entity_id(uri=uri) for uri in self.child_uris]

    @property
    def child_count(self) -> int:
        return len(self.child_ids)

    @property
    def residual(self) -> Optional[str]:
        test = get_entity_id(self.foundation_uri)
        if test in ("other", "unspecified"):
            return test
        return None

    @property
    def is_residual(self):
        return bool(self.residual)

    @property
    def is_leaf(self):
        return len(self.child_uris) == 0

    @classmethod
    def from_api(cls, entity_id: str, response_data: dict):
        if response_data is None:
            return None

        uri = response_data["@id"]
        uri_entity_id = response_data["@id"]
        response_data["entity_id"] = get_entity_id(uri=uri)

        if uri_entity_id in ("unspecified", "other"):
            response_data["entity_residual"] = entity_id
            response_data["entity_id"] = response_data["@id"].split("/")[-2]

        params, other = get_params_dicts(response_data=response_data, known_keys=entity_known_keys)
        params = flatten_labels(obj=params)
        entity = cls(**params, other=other, entity_id=entity_id)
        return entity

    def __repr__(self):
        return f"Entity {self.entity_id} - {self.title}"

    def to_dict(self):
        results = self.__dict__
        results = dict((key, value) for key, value in results.items() if value is not None and value != [])
        for key in ["context", "request_uri", "request_uris"]:
            results.pop(key, None)
        return results

    def to_json(self):
        return json.dumps(self.to_dict())
