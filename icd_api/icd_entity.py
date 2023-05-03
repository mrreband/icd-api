from dataclasses import dataclass

from icd_api.icd_util import get_mms_uri, get_foundation_uri, get_entity_id

entity_known_keys = [
    "title", "definition", "longDefinition", "fullySpecifiedName", "diagnosticCriteria", "child", "parent",
    "ancestor", "descendant", "synonym", "narrowerTerm", "inclusion", "exclusion", "browserUrl",
]


@dataclass
class ICDEntity:
    entity_id: str
    title: str
    definition: str = None
    longDefinition: str = None
    fullySpecifiedName: str = None
    diagnosticCriteria: str = None
    child: list = None
    parent: list = None
    ancestor: list = None
    descendant: list = None
    synonym: list = None
    narrowerTerm: list = None
    inclusion: list = None
    exclusion: list = None
    browserUrl: str = None

    # custom attributes
    entity_residual: str = None  # if the uri ends with unspecified or other, store that here
    residuals: dict = None  # results of icd_api.get_residuals go here
    lookup: dict = None  # results of icd_api.lookup go here
    depth: int = None  # how many parents

    # place to store any response data not itemized above
    other: dict = None

    @property
    def request_type(self):
        return "entity"

    @property
    def foundation_uri(self):
        return get_foundation_uri(entity_id=self.entity_id)

    @property
    def linearization_release_uri(self):
        return get_mms_uri(entity_id=self.entity_id)

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
    def residual(self) -> str or None:
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
        uri = response_data["@id"]
        uri_entity_id = response_data["@id"]
        response_data["entity_id"] = get_entity_id(uri=uri)

        if uri_entity_id in ("unspecified", "other"):
            response_data["entity_residual"] = entity_id
            response_data["entity_id"] = response_data["@id"].split("/")[-2]

        params = dict((k, v) for k, v in response_data.items() if k in entity_known_keys)
        other = dict((k, v) for k, v in response_data.items() if k not in entity_known_keys)
        entity = cls(**params, other=other, entity_id=entity_id)

        # todo: entity_id is provided to safeguard against residuals - requested id might not match response id
        # todo: child_ids may contain "other" and "unspecified"
        return entity

    def __repr__(self):
        return f"Entity {self.entity_id} - {self.title}"

    def to_json(self):
        results = self.__dict__
        results = dict((key, value) for key, value in results.items() if value is not None and value != [])
        for key in ["context", "request_uri", "request_uris"]:
            results.pop(key, None)
        return results
