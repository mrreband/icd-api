from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Entity:
    entity_id: str
    entity_label: str
    parent_ids: list
    request_uri: str = None
    context: str = None
    child_ids: list = None

    # optional fields - entity results only
    entity_child_uris: list = None
    synonyms: list = None

    # optional fields - may appear in entity or lookup results
    inclusions: list = None
    exclusions: list = None

    # optional fields - lookup results only
    lookup_child_uris: list = None
    entity_residual: str = None
    lookup_id_match: bool = None
    index_terms: list = None
    related_entities_in_perinatal_chapter: list = None
    foundation_child_elsewhere: list = None

    mms_code: str = None
    mms_block: str = None
    mms_class_kind: str = None
    mms_depth: str = None
    mms_chapter: str = None

    # extra fields for reporting
    residuals: dict = None  # child Y- and Z- codes if they exist
    lineage: dict = None    # itemized relationships with parent entities
    max_code_record: dict = None
    max_child_code: str = None
    proposed_code: str = None
    proposed_code_depth: int = None

    # place to store any response data not itemized above
    known_keys = ["@context", "browserUrl", "@id", "title", "parent", "child", "relatedEntitiesInPerinatalChapter",
                  "foundationChildElsewhere", "synonym", "exclusion", "indexTerm"]
    other: dict = None

    @property
    def request_type(self):
        """entities may be created from the response of either Api.get_entity or by Api.lookup"""
        if "/lookup?" in self.request_uri:
            return "lookup"
        return "entity"

    @property
    def foundation_uri(self):
        return f"http://id.who.int/icd/entity/{self.entity_id}"

    @property
    def linearization_release_uri(self):
        return f"http://id.who.int/icd/release/11/beta/mms/{self.entity_id}"

    @property
    def parent_count(self) -> int:
        return len(self.parent_ids)

    @property
    def child_count(self) -> int:
        return len(self.child_ids)

    @property
    def indirect_children_ids(self) -> List[str]:
        """
        Some of the foundation_child_elsewhere results are actually children of this entity's parent,
        eg hypoxia - api.lookup('http://id.who.int/icd/entity/474887737')

        Only return the ids that are children of this entity
        """
        # use foundationReference as a default key, fall back on linearizationReference --
        # both should be there, and both should have the same trailing entity_id
        return [eid for eid in self.foundation_child_elsewhere_ids if eid in self.child_ids]

    @property
    def foundation_child_elsewhere_ids(self) -> List[str]:
        """
        in the foundation taxonomy, there is a parent-child relationship,
        but these are not direct children in the linearization
        """
        # use foundationReference as a default key, fall back on linearizationReference --
        # both should be there, and both should have the same trailing entity_id
        uris = [uri.get("foundationReference", uri["linearizationReference"])
                for uri in self.foundation_child_elsewhere]
        return [uri.split("/")[-1] for uri in uris]

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
    def node_color(self) -> str:
        if self.mms_code:
            return "blue"
        return "black"

    @property
    def node_filled(self) -> str:
        if len(self.child_ids) > 0:
            return "empty"
        return "filled"

    @property
    def node(self) -> str:
        return f"{self.node_filled} {self.node_color} circle"

    @classmethod
    def from_api(cls, entity_id: str, response_data: dict, request_uri: str = "entity"):
        def process_labels(values) -> List[str]:
            """extract just the text of a label"""
            return [value["label"]["@value"] for value in values]

        def process_inclusions(exclusions) -> List[Dict[str, str]]:
            """extract the label and foundation reference"""
            return [{"label": value["label"]["@value"], "foundationReference": value.get("foundationReference", None)}
                    for value in exclusions]

        def process_fcr(exclusions) -> List[Dict[str, str]]:
            """extract the label, foundation reference, linearization reference - both refs have the same entity id"""
            return [{"label": value["label"]["@value"],
                     "foundationReference": value.get("foundationReference", None),
                     "linearizationReference": value.get("linearizationReference", None)}
                    for value in exclusions]

        entity_id = response_data["@id"].split("/")[-1]
        entity_residual = None
        if entity_id in("unspecified", "other"):
            entity_residual = entity_id
            entity_id = response_data["@id"].split("/")[-2]

        parent_ids = [p.split("/")[-1] for p in response_data["parent"]]
        child_uris = response_data.get("child", [])
        child_ids = [uri.split("/")[-1] for uri in child_uris]

        # todo: child_ids may contain "other" and "unspecified"
        entity = Entity(
            request_uri=request_uri,
            entity_id=entity_id,
            entity_residual=entity_residual,
            context=response_data["@context"],
            entity_label=response_data["title"]["@value"],
            parent_ids=parent_ids,
            child_ids=child_ids,
            related_entities_in_perinatal_chapter=response_data.get("relatedEntitiesInPerinatalChapter", []),
            foundation_child_elsewhere=process_fcr(response_data.get("foundationChildElsewhere", [])),
            synonyms=process_labels(response_data.get("synonym", [])),
            inclusions=process_inclusions(response_data.get("inclusion", [])),
            exclusions=process_inclusions(response_data.get("exclusion", [])),
            index_terms=process_labels(response_data.get("indexTerm", []))
        )

        if entity.request_type == "lookup":
            lookup_id_match = entity_id == entity.entity_id
            entity.lookup_id_match = lookup_id_match
            entity.lookup_child_uris = child_uris
            if lookup_id_match:
                entity.mms_code = response_data.get("code", "")
                entity.mms_block = response_data.get("blockId", "")
                entity.mms_class_kind = response_data.get("classKind", "")
        else:
            entity.entity_child_uris = child_uris

        other_data = dict((k, v) for k, v in response_data.items() if k not in cls.known_keys)
        cls.other = other_data

        return entity

    def __repr__(self):
        return f"Entity {self.entity_id} - {self.entity_label}"

    def to_json(self):
        results = self.__dict__
        results = dict((key, value) for key, value in results.items() if value is not None and value != [])
        for key in ["context", "request_uri", "request_uris"]:
            results.pop(key, None)
        return results

    @property
    def entity_data(self):
        return dict(entity_id=self.entity_id,
                    entity_label=self.entity_label,
                    context=self.context,
                    parent_ids=self.parent_ids,
                    child_ids=self.child_ids,
                    entity_child_uris=self.entity_child_uris,
                    synonyms=self.synonyms,
                    inclusions=self.inclusions,
                    exclusions=self.exclusions,
                    related_entities_in_perinatal_chapter=self.related_entities_in_perinatal_chapter,
                    foundation_child_elsewhere=self.foundation_child_elsewhere,
                    request_uri=self.request_uri)

    @property
    def lookup_data(self):
        return dict(entity_id=self.entity_id,
                    entity_residual=self.entity_residual,
                    related_entities_in_perinatal_chapter=self.related_entities_in_perinatal_chapter,
                    foundation_child_elsewhere=self.foundation_child_elsewhere,
                    lookup_child_uris=self.lookup_child_uris,
                    inclusions=self.inclusions,
                    exclusions=self.exclusions,
                    index_terms=self.index_terms,
                    lookup_id_match=self.lookup_id_match,
                    request_uri=self.request_uri,
                    mms_code=self.mms_code,
                    mms_class_kind=self.mms_class_kind)


def combine_entities(entity_obj: Entity, lookup_obj: Entity):
    return {**entity_obj, **lookup_obj}
