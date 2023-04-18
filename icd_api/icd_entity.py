from dataclasses import dataclass


@dataclass
class Entity:
    request_uri: str
    entity_id: str
    entity_label: str
    parent_ids: list
    child_ids: list
    mms_code: str = None
    mms_parent_id: str = None
    mms_parent_code: str = None

    # other fields
    synonyms: list = None
    exclusions: list = None
    index_terms: list = None
    related_entities_in_perinatal_chapter: list = None
    foundation_child_elsewhere: list = None
    other: dict = None

    @property
    def node_color(self):
        if self.mms_code:
            return "blue"
        return "black"

    @property
    def node_filled(self):
        if len(self.child_ids) > 0:
            return "empty"
        return "filled"

    @property
    def node(self):
        return f"{self.node_filled} {self.node_color} circle"

    @property
    def parent_count(self):
        return len(self.parent_ids)

    @classmethod
    def from_api(cls, response_data: dict, request_uri: str = "entity", mms_data: dict = None):
        def process_labels(values):
            return [value["label"]["@value"] for value in values]
        def process_exclusions(exclusions):
            return [{"label": value["label"]["@value"], "foundationReference": value["foundationReference"]}
                    for value in exclusions]

        parent_ids = [p.split("/")[-1] for p in response_data["parent"]]
        child_uris = response_data.get("child", [])
        child_ids = [uri.split("/")[-1] for uri in child_uris]
        entity = Entity(
            request_uri=request_uri,
            entity_id=response_data["@id"].split("/")[-1],
            entity_label=response_data["title"]["@value"],
            parent_ids=parent_ids,
            child_ids=child_ids,
            related_entities_in_perinatal_chapter=response_data.get("relatedEntitiesInPerinatalChapter", []),
            foundation_child_elsewhere=response_data.get("foundationChildElsewhere", []),
            synonyms=process_labels(response_data.get("synonym", [])),
            exclusions=process_exclusions(response_data.get("exclusion", [])),
            index_terms=process_labels(response_data.get("indexTerm", []))
        )

        # mms data doesn't exist in the response for entity getter,
        # but the user can provide it, populate these fields too
        if mms_data:
            entity.mms_code = mms_data.get("mms_code", None)
            entity.mms_parent_id = mms_data.get("mms_parent_id", None)
            entity.mms_parent_code = mms_data.get("mms_parent_code", None)

        return entity

    def __repr__(self):
        return f"Entity {self.entity_id} - {self.entity_label}"

    @property
    def request_type(self):
        if "/lookup?" in self.request_uri:
            return "lookup"
        return "entity"
