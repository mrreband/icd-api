from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Entity:
    request_uri: str
    context: str
    entity_id: str
    entity_label: str
    parent_ids: list
    child_ids: list

    # optional fields - entity results only
    synonyms: list = None

    # optional fields - may appear in entity or lookup results
    inclusions: list = None
    exclusions: list = None

    # optional fields - lookup results only
    lookup_id_match: bool = None
    index_terms: list = None
    related_entities_in_perinatal_chapter: list = None
    foundation_child_elsewhere: list = None

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
    def parent_count(self) -> int:
        return len(self.parent_ids)

    @property
    def child_count(self) -> int:
        return len(self.child_ids)

    @property
    def direct_child_count(self) -> int:
        """number of children that define this entity as their parent in the linearization"""
        return len(self.child_ids) - len(self.foundation_child_elsewhere)

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

        parent_ids = [p.split("/")[-1] for p in response_data["parent"]]
        child_uris = response_data.get("child", [])
        child_ids = [uri.split("/")[-1] for uri in child_uris]
        entity = Entity(
            request_uri=request_uri,
            entity_id=response_data["@id"].split("/")[-1],
            context=response_data["@context"],
            entity_label=response_data["title"]["@value"],
            parent_ids=parent_ids,
            child_ids=child_ids,
            related_entities_in_perinatal_chapter=response_data.get("relatedEntitiesInPerinatalChapter", []),
            foundation_child_elsewhere=response_data.get("foundationChildElsewhere", []),
            synonyms=process_labels(response_data.get("synonym", [])),
            inclusions=process_inclusions(response_data.get("inclusion", [])),
            exclusions=process_inclusions(response_data.get("exclusion", [])),
            index_terms=process_labels(response_data.get("indexTerm", []))
        )

        if entity.request_type == "lookup":
            entity.lookup_id_match = entity_id == entity.entity_id

        other_data = dict((k, v) for k, v in response_data.items() if k not in cls.known_keys)
        cls.other = other_data

        return entity

    def __repr__(self):
        return f"Entity {self.entity_id} - {self.entity_label}"

    def to_json(self):
        results = self.__dict__
        results.pop("context", None)
        return dict((key, value) for key, value in results.items() if value)

    @property
    def entity_data(self):
        return dict(entity_id=self.entity_id,
                    entity_label=self.entity_label,
                    context=self.context,
                    parent_ids=self.parent_ids,
                    child_ids=self.child_ids,
                    synonyms=self.synonyms,
                    inclusions=self.inclusions,
                    exclusions=self.exclusions,
                    request_uri=self.request_uri)

    @property
    def lookup_data(self):
        return dict(entity_id=self.entity_id,
                    related_entities_in_perinatal_chapter=self.related_entities_in_perinatal_chapter,
                    foundation_child_elsewhere=self.foundation_child_elsewhere,
                    inclusions=self.inclusions,
                    exclusions=self.exclusions,
                    index_terms=self.index_terms,
                    lookup_id_match=self.lookup_id_match,
                    request_uri=self.request_uri)


def combine_entities(entity_obj: Entity, lookup_obj: Entity):
    return {**entity_obj, **lookup_obj}
