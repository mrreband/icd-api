"""
read in the entities tree structure, flatten it, and write it back out for easier processing later
"""
import os

from dotenv import load_dotenv, find_dotenv

from icd_api import Api
from icd_api.icd11_foundation_entities import load_root_entity
from icd_api.util import load_json, write_csv, write_json

load_dotenv(find_dotenv())

api = Api()
api.set_linearization("mms")

output_folder = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_folder, exist_ok=True)


def dedupe(entities: list):
    """
    get_flattened_entities tries to remove duplicates but sometimes two recurson paths have the same entity,
    and they don't know about each other
    """
    print("deduping entities")
    deduped = []
    for entity in entities:
        if entity["entity_id"] not in [e["entity_id"] for e in deduped]:
            deduped.append(entity)
    return deduped


def get_flattened_entities():
    json_path = os.path.join(output_folder, "entities.json")
    if os.path.exists(json_path):
        print("loading flattened entities from json")
        return load_json(json_path)

    def get_entities_recurse(tree, unfurled):
        # pop the child tree structure, but leave child_ids for reference
        children = tree.pop("child_entities") or []
        child_ids = [c["entity_id"] for c in children]
        tree["child_ids"] = child_ids

        # don't process the same child entities multiple times
        existing_ids = [e["entity_id"] for e in unfurled]
        children = [c for c in children if c["entity_id"] not in existing_ids]

        unfurled.append(tree)
        for child in children:
            get_entities_recurse(tree=child, unfurled=unfurled)

        return unfurled

    print("loading nested entities from json")
    data = load_root_entity()
    entity_tree = data["entities"]
    entities = get_entities_recurse(entity_tree[0], [])

    write_json(entities, json_path)
    return entities


def write_entities_csv(entities: list):
    print("writing entities csv")
    for entity in entities:
        entity["parent_ids"] = "|".join(entity.get("parent_ids", []))
        entity["child_ids"] = "|".join(entity.get("child_ids", []))
    csv_path = os.path.join(output_folder, "entities.csv")
    write_csv(entities, csv_path)


if __name__ == '__main__':
    entities = get_flattened_entities()
    entities = dedupe(entities)
    entity_ids = [e["entity_id"] for e in entities]
    write_entities_csv(entities=entities)
