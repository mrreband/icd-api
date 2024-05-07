import json
from dataclasses import dataclass, field
from typing import List, Optional

from icd_api.linearization import Linearization
from icd_api.icd_util import get_entity_id, get_params_dicts, get_linearization_uri, flatten_labels

lookup_known_keys = [
    "entity_id", "title", "definition", "longDefinition", "fullySpecifiedName", "diagnosticCriteria",
    "source", "code", "codingNote", "blockId", "codeRange", "classKind", "child", "parent", "ancestor",
    "descendant", "foundationChildElsewhere", "indexTerm", "inclusion", "exclusion", "postcoordinationScale",
    "relatedEntitiesInMaternalChapter", "relatedEntitiesInPerinatalChapter"
]


@dataclass
class LinearizationEntity:
    # this is the requested uri, provided as a param when instantiated
    request_uri: str

    # this is the response @id, provided as a uri from the api.  it may not always match the request_uri
    response_id_uri: str

    linearization: Linearization
    title: str

    definition: Optional[str] = None
    long_definition: Optional[str] = None
    fully_specified_name: Optional[str] = None
    diagnostic_criteria: Optional[str] = None
    source: Optional[str] = None
    code: Optional[str] = None
    coding_note: Optional[str] = None
    block_id: Optional[str] = None
    code_range: Optional[str] = None
    class_kind: Optional[str] = None
    parent: list = field(default_factory=list)
    child: list = field(default_factory=list)
    ancestor: list = field(default_factory=list)
    descendant: list = field(default_factory=list)
    foundation_child_elsewhere: list = field(default_factory=list)
    index_term: list = field(default_factory=list)
    inclusion: list = field(default_factory=list)
    exclusion: list = field(default_factory=list)
    postcoordination_scale: list = field(default_factory=list)
    related_entities_in_maternal_chapter: list = field(default_factory=list)
    related_entities_in_perinatal_chapter: list = field(default_factory=list)
    browser_url: Optional[str] = None

    # place to store any response data not itemized above
    other: dict = field(default_factory=dict)

    def __repr__(self):
        response = f"Lookup {self.request_id} ({self.response_type}) - "
        if self.lookup_id_match:
            response += f" {self.title}"
        else:
            response += f" (response id {self.response_id})"
        response += f" - {self.title}"
        if self.code:
            response += f" (mms {self.class_kind} {self.code})"
        return response

    @property
    def request_id(self) -> str:
        return get_entity_id(self.request_uri)

    @property
    def response_id(self) -> str:
        candidate_id = get_entity_id(self.response_id_uri)
        if candidate_id not in ('other', 'unspecified'):
            return candidate_id
        return "/".join(self.response_id_uri.split("/")[-2:])

    @property
    def entity_id(self) -> str:
        if not self.lookup_id_match:
            raise ValueError(f"mismatched ids - {self.request_id} != {self.response_id_uri}")

        return self.request_id

    @property
    def request_type(self) -> str:
        return "lookup"

    @property
    def linearization_release_uri(self) -> str:
        return get_linearization_uri(entity_id=self.entity_id, linearization_name=self.linearization.name)

    @property
    def parent_uris(self) -> list[str]:
        return self.parent

    @property
    def parent_ids(self) -> list[str]:
        return [get_entity_id(uri=uri) for uri in self.parent_uris]

    @property
    def parent_id(self) -> str:
        if len(self.parent) > 1:
            raise ValueError("more than one parent")
        return self.parent_ids[0]

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
        test = get_entity_id(self.response_id_uri)
        if test in ("other", "unspecified"):
            return test
        return None

    @property
    def is_residual(self) -> bool:
        return bool(self.residual)

    @property
    def is_leaf(self) -> bool:
        return len(self.child_uris) == 0

    @property
    def lookup_id_match(self) -> bool:
        return self.request_id == self.response_id

    @property
    def response_type(self) -> str:
        """
        One of three distinct response types when calling the /lookup endpoint
        """
        # If the foundation entity is included in the linearization and has a code
        # then that linearization entity is returned.
        if self.lookup_id_match:
            return "in_linearization"

        # If the foundation entity in included in the linearization but it is a grouping without a code
        # then the system will return the unspecified residual category under that grouping.
        if self.code and self.code.upper().endswith("Z"):
            return "linearization_grouping"

        # If the entity is not included in the linearization
        # then the system checks where that entity is aggregated to and then returns that entity.
        return "not_in_linearization"

    @classmethod
    def from_api(cls, linearization: Linearization, request_uri: str, response_data: dict) -> "LinearizationEntity":
        """
        Use the json response data from a lookup call to instantiate and return an ICDLookup object
        """
        if response_data is None:
            raise ValueError("no response_data")
        params, other = get_params_dicts(response_data=response_data, known_keys=lookup_known_keys)
        params["response_id_uri"] = response_data.get("@id", "")
        params = flatten_labels(obj=params)

        obj = cls(**params, linearization=linearization, other=other, request_uri=request_uri)
        return obj

    @property
    def foundation_child_elsewhere_ids(self) -> List[str]:
        """
        in the foundation taxonomy, there is a parent-child relationship,
        but these are not direct children in the linearization
        """
        # use foundationReference as a default key, fall back on linearizationReference --
        # both should be there, and both should have the same trailing entity_id
        uris = [uri.get("foundationReference", uri["linearizationReference"])
                for uri in self.foundation_child_elsewhere or []]
        return [uri.split("/")[-1] for uri in uris]

    @property
    def indirect_children_ids(self) -> List[str]:
        """
        Some foundation_child_elsewhere results are actually children of this entity's parent,
        eg hypoxia - api.lookup('http://id.who.int/icd/entity/474887737')

        Only return the ids that are children of this entity
        """
        # use foundationReference as a default key, fall back on linearizationReference --
        # both should be there, and both should have the same trailing entity_id
        return [eid for eid in self.foundation_child_elsewhere_ids if eid in self.child_ids]

    @property
    def direct_children_ids(self) -> List[str]:
        """
        direct children in both the taxonomy and in linearization
        """
        return [child_id for child_id in self.child_ids if child_id not in self.indirect_children_ids]

    @property
    def direct_child_count(self) -> int:
        """number of children that define this entity as their parent in the linearization"""
        return len(self.direct_children_ids)

    @property
    def descendant_ids(self) -> List[str]:
        return [get_entity_id(uri) for uri in self.descendant or []]

    @property
    def ancestor_ids(self) -> List[str]:
        return [get_entity_id(uri) for uri in self.ancestor or []]

    @property
    def index_term_uris(self) -> List[str]:
        index_terms = self.index_term or []
        foundation_refs = [it for it in index_terms if "foundationReference" in it.keys()]
        return [fr["foundationReference"] for fr in foundation_refs]

    @property
    def index_term_ids(self) -> List[str]:
        return [get_entity_id(uri) for uri in self.index_term_uris]

    @property
    def node_color(self) -> str:
        if self.response_type in ["in_linearization", "linearization_grouping"]:
            return "blue"
        return "black"

    @property
    def node_filled(self) -> Optional[str]:
        if self.class_kind is None:
            return None
        if self.class_kind in ["block", "chapter"]:
            return "empty"
        return "filled"

    @property
    def node(self) -> str:
        return f"{self.node_filled} {self.node_color} circle"

    def to_dict(self, include_props: Optional[list] = None, exclude_attrs: Optional[list] = None) -> dict:
        results = self.__dict__
        results = dict((key, value) for key, value in results.items() if value is not None and value != [])
        results["linearization"] = results["linearization"].__dict__

        if exclude_attrs is None:
            exclude_attrs = []
        for key in exclude_attrs:
            results.pop(key, None)

        if include_props is None:
            include_props = []
        for include_prop in include_props:
            results[include_prop] = getattr(self, include_prop)

        return results

    def to_json(self):
        return json.dumps(self.to_dict())
