from dataclasses import dataclass


@dataclass
class Entity:
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
    def from_api(cls, response_data: dict, mms_data: dict = None):
        parent_ids = [p.split("/")[-1] for p in response_data["parent"]]
        child_uris = response_data.get("child", [])
        child_ids = [uri.split("/")[-1] for uri in child_uris]
        entity = Entity(
            entity_id=response_data["@id"].split("/")[-1],
            entity_label=response_data["title"]["@value"],
            parent_ids=parent_ids,
            child_ids=child_ids,
        )

        if "synonym" in response_data.keys():
            values = response_data["synonym"]
            values = [value["label"]["@value"] for value in values]
            cls.synonyms = values
        if "exclusion" in response_data.keys():
            values = response_data["exclusion"]
            values = [{"label": value["label"]["@value"], "foundationReference": value["foundationReference"]}
                      for value in values]
            cls.exclusions = values

        # mms data doesn't exist in the response for entity getter,
        # but the user can provide it, populate these fields too
        if mms_data:
            entity.mms_code = mms_data.get("mms_code", None)
            entity.mms_parent_id = mms_data.get("mms_parent_id", None)
            entity.mms_parent_code = mms_data.get("mms_parent_code", None)

        return entity

    def __repr__(self):
        return f"Entity {self.entity_id} - {self.entity_label}"
